import json
from importlib import import_module

from pydantic import BaseModel

from app.secbot.schemas import PYDANTIC_CLS_PATH


def load_cls(path: str) -> BaseModel:
    """Load a class from a path"""
    module, class_name = path.rsplit(".", 1)
    return getattr(import_module(module), class_name)


def serializer(values):
    """Convert JSON-serializable objects back into original data types.

    This function recursively handles the conversion of input values,
    such as dictionaries for Pydantic models, into their original data types.
    by checking for a special key in the dictionary which
    is essentially putted by the deserializer function.
    """
    if isinstance(values, (list, tuple)):
        return tuple(serializer(value) for value in values)
    if isinstance(values, dict):
        if PYDANTIC_CLS_PATH in values.keys():
            cls = load_cls(values.get(PYDANTIC_CLS_PATH))
            return cls.parse_obj(values)
        else:
            return {key: serializer(value) for key, value in values.items()}
    return values


def deserializer(values):
    """Convert values into JSON-serializable objects.

    This function handles the conversion of values, such as Pydantic models,
    into JSON-serializable objects.
    For Pydantic models, it creates a dictionary with a special key storing the model's path,
    allowing for easy re-serialization before a Celery task execution.
    """
    if isinstance(values, (list, tuple)):
        return tuple(deserializer(value) for value in values)
    if isinstance(values, dict):
        return {key: deserializer(value) for key, value in values.items()}
    if issubclass(type(values), BaseModel):
        return json.loads(values.json())
    return values
