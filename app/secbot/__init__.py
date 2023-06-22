import importlib
import inspect
import os
import pkgutil
from typing import Type

from celery import Celery

from .inputs import SecbotInput
from .logger import logger
from .schemas import SecurityCheckStatus


class SecurityBot:
    """
    Main class for the SecurityBot application. Manages inputs for security checks,
    runs these checks, and fetches check results.

    Attributes:
        celery_app: Celery application instance for managing asynchronous tasks.
        _registered_inputs: Dictionary of registered inputs (security checks).
    """

    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self._registered_inputs = {}  # Contains the registered inputs
        self.autodiscover_inputs()

    def autodiscover_inputs(self):
        """
        Automatically discover all available inputs (security checks)
        from the inputs module, and register them to the bot.
        """
        base_package = "app.secbot.inputs"
        base_path = os.path.dirname(__import__(base_package, fromlist=[""]).__file__)

        # Iterate over all modules in the base package
        for _, package_name, _ in pkgutil.iter_modules([base_path]):
            full_package_name = f"{base_package}.{package_name}"
            try:
                module = importlib.import_module(full_package_name)
            except ImportError as e:
                logger.warning(
                    f"Could not import {full_package_name}. Error: {str(e)}"
                )
                continue

            # Register all classes that are a subclass of SecbotInput (excluding SecbotInput itself)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, SecbotInput) and cls != SecbotInput:
                    self.register_input(package_name, cls)

    def register_input(self, config_name: str, input_cls: Type[SecbotInput]):
        """
        Register a new input (security check) to the bot.

        Args:
            config_name: The name of the configuration for the input.
            input_cls: The class representing the input.
        """
        self._registered_inputs[config_name] = input_cls(
            config_name=config_name,
            celery_app=self.celery_app,
        )

    async def run(self, input_name: str, *args, **kwargs):
        """
        Run a registered input (security check).

        Args:
            input_name: The name of the input to run.
            args, kwargs (optional): Arguments to pass to the input's run method.
        """
        registered_input = self._registered_inputs[input_name]
        await registered_input.run(*args, **kwargs)

    async def fetch_check_result(
        self,
        input_name,
        *args,
        **kwargs,
    ) -> SecurityCheckStatus:
        """
        Fetch the result of a security check.

        Args:
            input_name: The name of the input whose result to fetch.
            args, kwargs (optional): Arguments to pass to the input's fetch_result method.
        Returns:
            The status of the security check.
        """
        registered_input = self._registered_inputs[input_name]
        return await registered_input.fetch_status(*args, **kwargs)
