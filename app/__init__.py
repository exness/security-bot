import logging
from typing import Optional

from celery.app.log import TaskFormatter


def format_extra(message, extra: Optional[dict] = None):
    """Format extra keys from record.__dict__"""
    if not extra:
        return message
    extra_str = ", ".join(f"{k}={str(v)[:15]}" for k, v in extra.items())
    return f"{message} EXTRA: {extra_str}"


class ExtraLogFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return format_extra(message, record.__dict__)


class ExtraTaskFormatter(TaskFormatter):
    def format(self, record):
        message = super().format(record)
        return format_extra(message, record.__dict__)
