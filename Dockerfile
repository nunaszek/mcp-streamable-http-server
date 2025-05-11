# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy the dependency lock file and project configuration
COPY uv.lock pyproject.toml ./

# Install project dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# The server.main:run script is defined in pyproject.toml
CMD ["uv", "run", "server"] 