import logging.config
import typing

import sentry_sdk
import yaml
from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app import ExtraTaskFormatter
from app.exceptions.api_errors import APIError
from app.exceptions.handlers import (
    api_error_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.exceptions.schemas import ValidationError
from app.metrics.celery import instrument as celery_metrics_instrument
from app.metrics.server import ASGIMetricsMiddleware
from app.routers import gitlab, healthcheck, metrics, security
from app.settings import BASE_PATH, flatten_settings_values, settings


def init_celery() -> Celery:
    celery = Celery(__name__)
    celery.conf.broker_url = settings.celery_broker_url
    celery.conf.result_backend = settings.celery_result_backend
    celery_metrics_instrument()

    return celery


def sanitize_event_values(
    value: typing.Union[dict, list, tuple, str],
    sensitive_values: typing.Set[typing.Union[str, int]],
) -> typing.Union[dict, list, tuple, str]:
    """Sanitize a sentry event from sensitive values.

    A sentry event is a complex dictionary of problem information.
    This function goes recursively over all strings and replaces
    the sensitive ones with the word [Redacted]
    """
    if isinstance(value, dict):
        value = {
            k: sanitize_event_values(v, sensitive_values) for k, v in value.items()
        }
    elif isinstance(value, list):
        value = [sanitize_event_values(item, sensitive_values) for item in value]
    elif isinstance(value, str):
        for sens_value in sensitive_values:
            sens_value = str(sens_value)
            if sens_value in value:
                value = value.replace(sens_value, "[Redacted]")
    return value


def before_send(event, hint):
    """Sentry hook before sending an error handler.

    If you need to change something before sending an event to the sentry this is the place.
    https://docs.sentry.io/platforms/python/configuration/filtering/#filtering-error-events

    Here we redact all sensitive values from the event with
    all env variables from the app settings object.
    """
    settings_values = flatten_settings_values(app_settings=settings)
    event = sanitize_event_values(event, sensitive_values=settings_values)
    return event


def initial_secbot(celery_application):
    """Initializes the secbot workflow runner with auto-discovery.
    This process finds and registers workflow components.

    Although a workflow could run independently, it's advised to register and
    execute it through the runner for proper management.

    Args:
        celery_application: The Celery application for task management.

    Returns:
        An initialized instance of the SecurityBot class.
    """
    from app.secbot import SecurityBot

    return SecurityBot(celery_app=celery_application)


def init_app(
    title: str,
    routers: typing.List[APIRouter],
    openapi_tags: typing.List[typing.Dict[str, typing.Any]] = None,
):
    application = FastAPI(
        title=title,
        debug=settings.debug,
        version="1.0.0",
        docs_url="/docs" if settings.docs_enable else None,
        openapi_tags=openapi_tags,
    )

    # Setup exceptions
    application.add_exception_handler(
        APIError,
        api_error_exception_handler,
    )
    application.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    # Setup routes
    application.include_router(healthcheck.router)

    router_v1 = APIRouter(
        prefix="/v1",
        responses={
            422: {
                "model": ValidationError,
                "description": "Validation Error",
            }
        },
    )
    for router in routers:
        router_v1.include_router(router)

    application.include_router(router_v1)

    # Setup metrics
    application.add_middleware(
        ASGIMetricsMiddleware,
        tier=1,
        include_latency_histogram=True,
        record_source_ip=True,
        include_not_found_url_label=False,
    )
    application.include_router(metrics.router)

    # Setup sentry
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, before_send=before_send)

    return application


with open(BASE_PATH / "logging.yml") as logging_yml:
    logging_config = yaml.safe_load(logging_yml.read())
    logging.config.dictConfig(logging_config)

app = init_app(
    title=settings.app_name,
    routers=[
        gitlab.router,
    ],
    openapi_tags=[
        {"name": "common"},
        {
            "name": "gitlab",
            "externalDocs": {
                "description": "Gitlab webhook events",
                "url": "https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html",
            },
        },
    ],
)
security_gateway_app = init_app(
    title="Security Gateway",
    routers=[security.router],
    openapi_tags=[{"name": "common"}, {"name": "security"}],
)
celery_app = init_celery()
security_bot = initial_secbot(celery_app)


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    with open(BASE_PATH / "logging.yml") as logging_yml:
        logging_config = yaml.safe_load(logging_yml.read())
        logging.config.dictConfig(logging_config)


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        if handler.formatter:
            # Change the formatter but leave the format be.
            formatter = ExtraTaskFormatter(handler.formatter._fmt)
            handler.setFormatter(formatter)
