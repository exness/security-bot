import pytest
from faker import Faker
from pydantic import BaseModel, BaseSettings, SecretStr
from starlette.testclient import TestClient

from app.main import app  # noqa
from tests.units.common import get_test_root_directory


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def dir_tests():
    return get_test_root_directory()


@pytest.fixture(scope="session")
def celery_config():
    return {"task_always_eager": True}


@pytest.fixture
def example_settings():
    class ExampleModel(BaseModel):
        title: str = "model"
        secret: SecretStr = "secret"

    class ExampleSettings(BaseSettings):
        title: str = "app"
        model: ExampleModel = ExampleModel()
        dictionary: dict = {"hello": "world"}

    return ExampleSettings()


@pytest.fixture
def faker():
    return Faker()
