import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import List, Type
from .base import BaseService

logger = logging.getLogger(__name__)

class ServiceLoader:
    """
    Discovers, loads, and manages the lifecycle of services derived from BaseService.
    """
    def __init__(self, services_package_name: str = "service"):
        """
        Initializes the ServiceLoader.

        Args:
            services_package_name: The full dotted name of the package where services are located
                                   (e.g., "project_name.services_module").
        """
        self.services_package_name = services_package_name
        self._service_instances: List[BaseService] = []
        logger.info(f"ServiceLoader initialized for package '{services_package_name}'.")

    def discover_and_load_services(self) -> None:
        """
        Discovers service classes within the specified package, instantiates them,
        and stores them for management.
        Services are classes that inherit from BaseService and are not abstract.
        """
        logger.info(f"Discovering services in package '{self.services_package_name}'...")
        try:
            package = importlib.import_module(self.services_package_name)
        except ImportError as e:
            logger.error(f"Failed to import service package '{self.services_package_name}': {e}", exc_info=True)
            return

        if not hasattr(package, '__path__'):
            logger.error(f"Package '{self.services_package_name}' has no __path__ attribute. "
                         f"Ensure it's a package with an __init__.py and not just a module.")
            return
            
        package_paths = package.__path__

        for path_entry in package_paths:
            module_prefix = package.__name__ + '.'
            logger.debug(f"Scanning path: {path_entry} with prefix {module_prefix}")
            for module_info in pkgutil.walk_packages([str(path_entry)], prefix=module_prefix):
                if module_info.name == __name__ or module_info.name.endswith('.base_service') or module_info.name.endswith('.service_loader'):
                    logger.debug(f"Skipping module: {module_info.name} (utility module)")
                    continue
                try:
                    module = importlib.import_module(module_info.name)
                    logger.debug(f"Scanning module: {module_info.name}")
                    for name, obj_type in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj_type, BaseService) and \
                           obj_type is not BaseService and \
                           not inspect.isabstract(obj_type):
                            try:
                                instance = obj_type()
                                self._service_instances.append(instance)
                                logger.info(f"Successfully loaded and instantiated service: {name} from {module_info.name}")
                            except Exception as e:
                                logger.error(f"Failed to instantiate service class '{name}' from module '{module_info.name}': {e}", exc_info=True)
                except ImportError as e:
                    logger.error(f"Failed to import module '{module_info.name}': {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"An unexpected error occurred while processing module '{module_info.name}': {e}", exc_info=True)
        
        if not self._service_instances:
            logger.warning(f"No services were found or loaded from '{self.services_package_name}'. "
                           "Ensure service classes exist, inherit from BaseService, are not abstract, and are in the correct package.")
        else:
            logger.info(f"Finished discovery. Found and instantiated {len(self._service_instances)} service(s).")


    @property
    def service_instances(self) -> List[BaseService]:
        """Returns the list of loaded service instances."""
        return self._service_instances

    async def start_all(self) -> None:
        """Starts all loaded services."""
        if not self._service_instances:
            logger.info("No services to start.")
            return
            
        logger.info(f"Starting {len(self._service_instances)} services...")
        for service in self._service_instances:
            service_name = type(service).__name__
            try:
                logger.debug(f"Starting service: {service_name}...")
                await service.start()
                logger.info(f"Service {service_name} started successfully.")
            except Exception as e:
                logger.error(f"Error starting service {service_name}: {e}", exc_info=True)
        logger.info("All services have been processed for startup.")

    async def release_all(self) -> None:
        """Releases all loaded services, typically in reverse order of startup."""
        if not self._service_instances:
            logger.info("No services to release.")
            return

        logger.info(f"Releasing {len(self._service_instances)} services...")
        for service in reversed(self._service_instances):
            service_name = type(service).__name__
            try:
                logger.debug(f"Releasing service: {service_name}...")
                await service.release()
                logger.info(f"Service {service_name} released successfully.")
            except Exception as e:
                logger.error(f"Error releasing service {service_name}: {e}", exc_info=True)
        logger.info("All services have been processed for release.") 