from __future__ import annotations

import pprint


class SecbotException(Exception):
    """Base gitlab exception class."""


class BaseGitlabWorkflowException(SecbotException):
    """Base gitlab exception with scan id info."""


class ScanCheckFailed(SecbotException):
    """Raises when we try to check scan status, and it's failed."""


class ScanCantBeScanned(SecbotException):
    """Raises when we try to scan a scan that already in progress."""


class ScanExecutionSkipped(SecbotException):
    """Raises when we want to make a scan skippable.

    It might happen when worker services can't proceed security check,
    and we don't want to set the scan status to ERROR.
    """


class SecbotInputError(SecbotException):
    """Base exception for all input exceptions."""


class SecbotConfigError(SecbotException):
    """This exception is raised when the configuration is invalid.

    It accumulates all possible errors that occur during the parsing of job
    configurations and presents them all at once.
    """

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return pprint.pformat(self.errors)


class SecbotConfigMissingEnv(SecbotConfigError):
    """This exception is raised when the configuration is missing an environment"""
