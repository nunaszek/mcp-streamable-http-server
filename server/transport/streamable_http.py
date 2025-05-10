"""
StreamableHTTP Server Transport Module

This module implements an HTTP transport layer with Streamable HTTP.

The transport handles bidirectional communication using HTTP requests and
responses, with streaming support for long-running operations.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from http import HTTPStatus

import anyio
from pydantic import ValidationError
from sse_starlette import EventSourceResponse
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

from mcp.shared.message import SessionMessage
from mcp.types import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    PARSE_ERROR,
    JSONRPCError,
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
)

from mcp.server.streamable_http import StreamableHTTPServerTransport

# Import for API key validation
from ..middleware.core import validate, RequestCredentialsContext

logger = logging.getLogger(__name__)

# Maximum size for incoming messages
MAXIMUM_MESSAGE_SIZE = 4 * 1024 * 1024  # 4MB

# Header names
MCP_SESSION_ID_HEADER = "mcp-session-id"
LAST_EVENT_ID_HEADER = "last-event-id"

# Content types
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_SSE = "text/event-stream"

# Special key for the standalone GET stream
GET_STREAM_KEY = "_GET_stream"

# Session ID validation pattern (visible ASCII characters ranging from 0x21 to 0x7E)
# Pattern ensures entire string contains only valid characters by using ^ and $ anchors
SESSION_ID_PATTERN = re.compile(r"^[\x21-\x7E]+$")

# Type aliases
StreamId = str
EventId = str


@dataclass
class EventMessage:
    """
    A JSONRPCMessage with an optional event ID for stream resumability.
    """

    message: JSONRPCMessage
    event_id: str | None = None


EventCallback = Callable[[EventMessage], Awaitable[None]]


class EventStore(ABC):
    """
    Interface for resumability support via event storage.
    """

    @abstractmethod
    async def store_event(
        self, stream_id: StreamId, message: JSONRPCMessage
    ) -> EventId:
        """
        Stores an event for later retrieval.

        Args:
            stream_id: ID of the stream the event belongs to
            message: The JSON-RPC message to store

        Returns:
            The generated event ID for the stored event
        """
        pass

    @abstractmethod
    async def replay_events_after(
        self,
        last_event_id: EventId,
        send_callback: EventCallback,
    ) -> StreamId | None:
        """
        Replays events that occurred after the specified event ID.

        Args:
            last_event_id: The ID of the last event the client received
            send_callback: A callback function to send events to the client

        Returns:
            The stream ID of the replayed events
        """
        pass


class FastStreamableHTTPServerTransport(StreamableHTTPServerTransport):

    def __init__(
        self,
        mcp_session_id: str | None,
        is_json_response_enabled: bool = False,
        event_store: EventStore | None = None,
    ) -> None:
        super().__init__(mcp_session_id, is_json_response_enabled, event_store)

    def _preprocess_tools_call_params(self, message: JSONRPCMessage) -> None:
        """
        Processes parameters for a 'tools/call' request, handling session ID
        updates and ensuring _meta consistency.
        Modifies message.root.params and self.mcp_session_id in place.
        """
        if not (
            isinstance(message.root, JSONRPCRequest)
            and message.root.method == "tools/call"
        ):
            return

        if isinstance(message.root.params, dict):
            if self.mcp_session_id:
                # Ensure _meta key exists before accessing it, initialize if not.
                meta_dict_in_params = message.root.params.setdefault("_meta", {})
                meta_dict_in_params["session_id"] = self.mcp_session_id

    async def _handle_post_request(
        self, scope: Scope, request: Request, receive: Receive, send: Send
    ) -> None:
        """Handle POST requests containing JSON-RPC messages."""
        writer = self._read_stream_writer
        if writer is None:
            raise ValueError(
                "No read stream writer available. Ensure connect() is called first."
            )
        try:
            # Check Accept headers
            has_json, has_sse = self._check_accept_headers(request)
            if not (has_json and has_sse):
                response = self._create_error_response(
                    (
                        "Not Acceptable: Client must accept both application/json and "
                        "text/event-stream"
                    ),
                    HTTPStatus.NOT_ACCEPTABLE,
                )
                await response(scope, receive, send)
                return

            # Validate Content-Type
            if not self._check_content_type(request):
                response = self._create_error_response(
                    "Unsupported Media Type: Content-Type must be application/json",
                    HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                )
                await response(scope, receive, send)
                return

            # Parse the body - only read it once
            body = await request.body()
            if len(body) > MAXIMUM_MESSAGE_SIZE:
                response = self._create_error_response(
                    "Payload Too Large: Message exceeds maximum size",
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                )
                await response(scope, receive, send)
                return

            try:
                raw_message = json.loads(body)
            except json.JSONDecodeError as e:
                response = self._create_error_response(
                    f"Parse error: {str(e)}", HTTPStatus.BAD_REQUEST, PARSE_ERROR
                )
                await response(scope, receive, send)
                return

            try:
                message = JSONRPCMessage.model_validate(raw_message)

            except ValidationError as e:
                response = self._create_error_response(
                    f"Validation error: {str(e)}",
                    HTTPStatus.BAD_REQUEST,
                    INVALID_PARAMS,
                )
                await response(scope, receive, send)
                return

            # Process tools/call specific logic which might update self.mcp_session_id
            # and message.root.params
            self._preprocess_tools_call_params(message)

            # Check if this is an initialization request
            is_initialization_request = (
                isinstance(message.root, JSONRPCRequest)
                and message.root.method == "initialize"
            )

            if is_initialization_request:
                # Check if the server already has an established session
                if self.mcp_session_id:
                    # Check if request has a session ID
                    request_session_id = self._get_session_id(request)

                    # Create credentials context
                    credentials_context = RequestCredentialsContext(
                        query_params=request.query_params,
                        headers=request.headers,
                        client_ip=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        session_id=request_session_id
                    )

                    # Validate credentials
                    if not validate(credentials_context):
                        response = self._create_error_response(
                            "Unauthorized: Invalid or missing credentials",
                            HTTPStatus.UNAUTHORIZED,
                        )
                        await response(scope, receive, send)
                        return

                    # If request has a session ID but doesn't match, return 404
                    if request_session_id and request_session_id != self.mcp_session_id:
                        response = self._create_error_response(
                            "Not Found: Invalid or expired session ID",
                            HTTPStatus.NOT_FOUND,
                        )
                        await response(scope, receive, send)
                        return

            # For non-initialization requests, validate the session
            elif not await self._validate_session(request, send):
                return

            # For notifications and responses only, return 202 Accepted
            if not isinstance(message.root, JSONRPCRequest):
                # Create response object and send it
                response = self._create_json_response(
                    None,
                    HTTPStatus.ACCEPTED,
                )
                await response(scope, receive, send)

                # Process the message after sending the response
                session_message = SessionMessage(message)
                await writer.send(session_message)

                return

            # Extract the request ID outside the try block for proper scope
            request_id = str(message.root.id)
            # Register this stream for the request ID
            self._request_streams[request_id] = anyio.create_memory_object_stream[
                EventMessage
            ](0)
            request_stream_reader = self._request_streams[request_id][1]

            if self.is_json_response_enabled:
                # Process the message
                session_message = SessionMessage(message)
                await writer.send(session_message)
                try:
                    # Process messages from the request-specific stream
                    # We need to collect all messages until we get a response
                    response_message = None

                    # Use similar approach to SSE writer for consistency
                    async for event_message in request_stream_reader:
                        # If it's a response, this is what we're waiting for
                        if isinstance(
                            event_message.message.root, JSONRPCResponse | JSONRPCError
                        ):
                            response_message = event_message.message
                            break
                        # For notifications and request, keep waiting
                        else:
                            logger.debug(
                                f"received: {event_message.message.root.method}"
                            )

                    # At this point we should have a response
                    if response_message:
                        # Create JSON response
                        response = self._create_json_response(response_message)
                        await response(scope, receive, send)
                    else:
                        # This shouldn't happen in normal operation
                        logger.error(
                            "No response message received before stream closed"
                        )
                        response = self._create_error_response(
                            "Error processing request: No response received",
                            HTTPStatus.INTERNAL_SERVER_ERROR,
                        )
                        await response(scope, receive, send)
                except Exception as e:
                    logger.exception(f"Error processing JSON response: {e}")
                    response = self._create_error_response(
                        f"Error processing request: {str(e)}",
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        INTERNAL_ERROR,
                    )
                    await response(scope, receive, send)
                finally:
                    await self._clean_up_memory_streams(request_id)
            else:
                # Create SSE stream
                sse_stream_writer, sse_stream_reader = (
                    anyio.create_memory_object_stream[dict[str, str]](0)
                )

                async def sse_writer():
                    # Get the request ID from the incoming request message
                    try:
                        async with sse_stream_writer, request_stream_reader:
                            # Process messages from the request-specific stream
                            async for event_message in request_stream_reader:
                                # Build the event data
                                event_data = self._create_event_data(event_message)
                                await sse_stream_writer.send(event_data)

                                # If response, remove from pending streams and close
                                if isinstance(
                                    event_message.message.root,
                                    JSONRPCResponse | JSONRPCError,
                                ):
                                    break
                    except Exception as e:
                        logger.exception(f"Error in SSE writer: {e}")
                    finally:
                        logger.debug("Closing SSE writer")
                        await self._clean_up_memory_streams(request_id)

                # Create and start EventSourceResponse
                # SSE stream mode (original behavior)
                # Set up headers
                headers = {
                    "Cache-Control": "no-cache, no-transform",
                    "Connection": "keep-alive",
                    "Content-Type": CONTENT_TYPE_SSE,
                    **(
                        {MCP_SESSION_ID_HEADER: self.mcp_session_id}
                        if self.mcp_session_id
                        else {}
                    ),
                }
                response = EventSourceResponse(
                    content=sse_stream_reader,
                    data_sender_callable=sse_writer,
                    headers=headers,
                )

                # Start the SSE response (this will send headers immediately)
                try:
                    # First send the response to establish the SSE connection
                    async with anyio.create_task_group() as tg:
                        tg.start_soon(response, scope, receive, send)
                        # Then send the message to be processed by the server
                        session_message = SessionMessage(message)
                        await writer.send(session_message)
                except Exception:
                    logger.exception("SSE response error")
                    await sse_stream_writer.aclose()
                    await sse_stream_reader.aclose()
                    await self._clean_up_memory_streams(request_id)

        except Exception as err:
            logger.exception("Error handling POST request")
            response = self._create_error_response(
                f"Error handling POST request: {err}",
                HTTPStatus.INTERNAL_SERVER_ERROR,
                INTERNAL_ERROR,
            )
            await response(scope, receive, send)
            if writer:
                await writer.send(Exception(err))
            return
