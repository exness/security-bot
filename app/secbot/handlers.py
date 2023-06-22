import abc
import asyncio
import functools
from typing import List, Optional, Type

from celery import Celery
from pydantic import BaseModel

from app.secbot import utils
from app.secbot.config import SecbotConfigComponent


def pydantic_celery_converter(func):
    """Decorator for asynchronous functions that use Pydantic models in their inputs or outputs.
    Serializes Pydantic models before the function is called and deserializes
    them after the function returns.

    Args:
        func: The asynchronous function to decorate.
    Returns:
        The decorated function.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        ret = await func(*utils.serializer(args), **utils.serializer(kwargs))
        return utils.deserializer(ret)

    return wrapper


class SecbotHandler(abc.ABC):
    """Abstract base class for SecbotHandler.
    It provides a unified interface for creating handlers
    for Secbot's various components (scans, outputs, notifications).

    Attributes:
        config_model: Optional Pydantic model for the handler's configuration.
        env_model: Optional Pydantic model for the handler's environment.
        celery_app: Celery application instance for managing asynchronous tasks.
        config_name: The name of the configuration for the handler.
        task: The Celery task corresponding to the handler.
    """

    config_model: Optional[Type[BaseModel]] = None
    env_model: Optional[Type[BaseModel]] = None

    def __init__(self, celery_app: Celery, config_name: str):
        self.celery_app = celery_app
        self.config_name = config_name

        def async_celery_task(*args, **kwargs):
            """Wrapper function that calls the handler's `run` method
            in an asyncio event loop.

            This function is used as the Celery task for this handler.
            """
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                pydantic_celery_converter(self.run)(*args, **kwargs)
            )

        def async_error_handler(task, exc, task_id, args, kwargs, einfo):
            """
            Error handler that calls the handler's `on_failure` method in
            an asyncio event loop in case of task failure.

            This function is set as the `on_failure` callback for the Celery task.
            """
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                pydantic_celery_converter(self.on_failure)(
                    *args,
                    exception=exc,
                    **kwargs,
                )
            )

        generate_task_name = f"secbot.handler.{self.config_name}"
        self.task = self.celery_app.task(
            name=generate_task_name,
            on_failure=async_error_handler,
        )(async_celery_task)

    async def on_failure(self, *args, **kwargs):
        """Async handler for task failure.

        Should be implemented in the subclasses as needed.

        Args:
            args: Positional arguments passed to the task that failed.
            kwargs: Keyword arguments passed to the task that failed.
        """

    @abc.abstractmethod
    async def run(self, *args, **kwargs):
        """Abstract method representing the main logic of the handler.

        Args:
            args: Positional arguments passed to the handler.
            kwargs: Keyword arguments passed to the handler.

        Raises:
            NotImplementedError: This method needs to be implemented in each subclass.
        """
        raise NotImplementedError


class SecbotScanHandler(SecbotHandler, abc.ABC):
    """Abstract base class for SecbotScanHandler.
    It inherits from SecbotHandler and provides a unified interface
    for creating scan handlers.

    Scan handlers are responsible for performing security scans.
    """


class SecbotOutputHandler(SecbotHandler, abc.ABC):
    """Abstract base class for SecbotOutputHandler. It inherits from SecbotHandler
    and provides a unified interface for creating output handlers.

    Output handlers are responsible for processing the results of the scans
    and outputting them to the specified destination.
    """

    @abc.abstractmethod
    async def fetch_status(
        self,
        *args,
        eligible_scans: List[SecbotConfigComponent],
        **kwargs,
    ) -> bool:
        """Abstract method to retrieve the status of the security check.
        Implemented in subclasses to fetch the status based on the specifics
        of the output (e.g., retrieving from a specific database, or API).

        Args:
            args: Positional arguments passed to the method.
            eligible_scans: List of eligible scans for the security check.
            kwargs: Keyword arguments passed to the method.

        Returns:
            bool: The status of the security check.

        Raises:
            NotImplementedError: This method needs to be implemented in each subclass.
        """
        raise NotImplementedError


class SecbotNotificationHandler(SecbotHandler, abc.ABC):
    """Abstract base class for SecbotNotificationHandler.
    It inherits from SecbotHandler and provides a unified interface
    for creating notification handlers.

    Notification handlers are responsible for sending notifications based
    on the results of the security checks.
    """
