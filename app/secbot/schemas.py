import enum

from pydantic import BaseModel, root_validator

PYDANTIC_CLS_PATH = "__pydantic_path_model__"


class SecbotBaseModel(BaseModel):
    """Base model for Secbot, supporting serialization/deserialization.

    This class extends the Pydantic BaseModel for use in Secbot's Celery
    workflow where models need to be serialized and deserialized.

    It ensures the inclusion of an absolute path to the class model in each
    instance, which is used later for deserialization.
    """

    @root_validator
    def populate_with_class_model(cls, values):
        """Populates the model with the absolute class model path.

        As a Pydantic root validator, it's invoked during validation for
        each model instance. It takes the model's attribute mapping, and
        adds a new entry under the `PYDANTIC_CLS_PATH` key. This path
        includes the module and class name, used later for deserialization.

        Args:
            values (dict): Model's attribute mapping.

        Returns:
            The updated attribute mapping.
        """
        values[PYDANTIC_CLS_PATH] = f"{cls.__module__}.{cls.__name__}"
        return values


class Severity(str, enum.Enum):
    # NOTE(ivan.zhirov): These severities are from defectdojo statuses.
    INFO = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

    @property
    def priority(self):
        # NOTE(valerio.rico): less => more important
        priorities = {
            self.INFO: 4,
            self.LOW: 3,
            self.MEDIUM: 2,
            self.HIGH: 1,
            self.CRITICAL: 0,
        }
        return priorities[self]


class SecurityCheckStatus(str, enum.Enum):
    """External secbot check status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ERROR = "error"  # an exception has happened.

    # All the data has been obtained.
    FAIL = "fail"  # we have vulnerabilities.
    SUCCESS = "success"  # we don't have vulnerabilities, or they are acceptable.


class ScanStatus(str, enum.Enum):
    """Internal (technical) secbot check status."""

    NEW = "new"
    IN_PROGRESS = "in_progress"
    SKIP = "skip"  # we decide to skip a scan for some reason.
    ERROR = "error"  # an exception has happened.
    DONE = "done"  # all the data has been obtained.
