import abc
import importlib
import inspect
import os
import pkgutil
from typing import Iterator, List, Type, Union

from celery import Celery
from celery.canvas import Signature, chain, group

from app.secbot import utils
from app.secbot.config import SecbotConfigComponent, WorkflowJob
from app.secbot.exceptions import SecbotInputError
from app.secbot.handlers import (
    SecbotHandler,
    SecbotNotificationHandler,
    SecbotOutputHandler,
    SecbotScanHandler,
)
from app.secbot.logger import logger
from app.secbot.schemas import ScanStatus, SecurityCheckStatus


class SecbotInput(abc.ABC):
    """
    Abstract base class for SecbotInput. It handles the discovery and registration
    of various handlers (scans, outputs, notifications) for each input.

    Attributes:
        config_name: The name of the configuration for the input.
        celery_app: Celery application instance for managing asynchronous tasks.
        scans: Dictionary of registered scan handlers.
        outputs: Dictionary of registered output handlers.
        notifications: Dictionary of registered notification handlers.
    """

    def __init__(self, config_name: str, celery_app: Celery):
        self.config_name = config_name
        self.celery_app = celery_app
        self.scans = {}
        self.outputs = {}
        self.notifications = {}

        self.autodiscover()

    def autodiscover(self):
        """
        Automatically discover all available handlers (scans, outputs, notifications)
        from the handlers module associated with this input, and register them.
        """
        try:
            base_package = f"app.secbot.inputs.{self.config_name}.handlers"
            base_path = os.path.dirname(
                __import__(base_package, fromlist=[""]).__file__
            )
        except ModuleNotFoundError:
            logger.warning(f"Could not find handlers for {self.config_name}")
            return

        handlers_cls = [
            SecbotScanHandler,
            SecbotOutputHandler,
            SecbotNotificationHandler,
        ]
        for _, package_name, _ in pkgutil.iter_modules([base_path]):
            full_package_name = f"{base_package}.{package_name}"
            try:
                module = importlib.import_module(full_package_name)
            except ImportError as e:
                logger.warning(
                    f"Could not import {full_package_name}. Error: {str(e)}"
                )
                continue
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, tuple(handlers_cls)) and cls not in handlers_cls:
                    self.register_handler(package_name, cls)

    def register_handler(
        self,
        handler_name: str,
        handler: Union[
            Type[SecbotScanHandler],
            Type[SecbotOutputHandler],
            Type[SecbotNotificationHandler],
        ],
    ):
        """Register a new handler (scan, output, or notification) to the input.

        Args:
            handler_name: The name of the handler to register.
            handler: The class representing the handler.
        """
        if issubclass(handler, SecbotScanHandler):
            components_group = self.scans
        elif issubclass(handler, SecbotOutputHandler):
            components_group = self.outputs
        elif issubclass(handler, SecbotNotificationHandler):
            components_group = self.notifications
        else:
            raise SecbotInputError(f"Handler {handler} is not a valid Secbot handler")

        components_group[handler_name] = handler(
            config_name=handler_name,
            celery_app=self.celery_app,
        )

    async def run(
        self,
        *args,
        job: WorkflowJob,
        **kwargs,
    ):
        """Run a secbot workflow by executing a series of consecutive steps.

        The job configuration contains all necessary information
        about the graph of dependencies.
        The scan function serves as the entry point for each path in the graph,
        and its results are sent to all registered outputs as configured by the job.

        Args:
            job: The WorkflowJob instance that specifies the workflow to be run.
            args: Positional arguments to be passed to the scan handler.
            kwargs: Keyword arguments to be passed to the scan handler.
        """

        def build_component_tasks(
            components_group: str,
            *component_args,
            **component_kwargs,
        ) -> Iterator[Signature]:

            for item in getattr(job, components_group):
                item: SecbotConfigComponent
                component: SecbotHandler = getattr(self, components_group)[
                    item.handler_name
                ]
                component_kwargs["component_name"] = item.name
                if component.env_model and item.env:
                    env_dict = item.env or {}
                    component_kwargs["env"] = component.env_model(**env_dict)
                if component.config_model:
                    config_dict = item.config or {}
                    component_kwargs["config"] = component.config_model(**config_dict)

                # Deserialize all pydantic models in the arguments and kwargs converts it
                # to json serializable objects
                prepared_args = utils.deserializer(component_args)
                prepared_kwargs = utils.deserializer(component_kwargs)

                yield component.task.s(*prepared_args, **prepared_kwargs)

        scan_tasks = list(build_component_tasks("scans", *args, **kwargs))
        output_tasks = list(build_component_tasks("outputs"))
        notification_tasks = list(build_component_tasks("notifications"))

        for scan_task in scan_tasks:
            for output_task in output_tasks:
                chain(
                    scan_task,
                    output_task,
                    group(notification_tasks),
                ).delay()

    async def fetch_status(
        self,
        outputs: List[SecbotConfigComponent],
        eligible_scans: List[SecbotConfigComponent],
        **kwargs,
    ) -> SecurityCheckStatus:
        """
        Fetch the status of the security checks associated with the given outputs.

        Args:
            eligible_scans: The scans that are eligible for the check.
            outputs: The outputs for which to fetch the status.
            kwargs: Additional keyword arguments to pass to the output handler.
        Returns:
            The status of the security checks (either SUCCESS or FAIL).
        """
        results: List[ScanStatus] = []
        for output in outputs:
            handler = self.outputs[output.handler_name]
            if handler.env_model:
                # Inject env model into kwargs like in output decorator
                kwargs["env"] = handler.env_model(**output.env)
            status = await handler.fetch_status(
                eligible_scans=eligible_scans, **kwargs
            )
            results.append(status)

        result = all(results)
        return SecurityCheckStatus.SUCCESS if result else SecurityCheckStatus.FAIL
