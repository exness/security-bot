from unittest import mock

from app.secbot.schemas import SecbotBaseModel
from app.secbot.utils import deserializer, load_cls, serializer


class Example(SecbotBaseModel):
    foo: str


def test_load_cls():
    cls = load_cls("tests.units.test_pydantic_celery.Example")
    assert cls == Example


def test_serializer_with_simple_value(faker):
    value = faker.pystr()
    assert value == serializer(value)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_serializer_with_pydantic_model(faker):
    model_path = "tests.units.test_pydantic_celery.Example"
    model = {"foo": "bar", "pydantic_field": model_path}
    assert Example(foo="bar") == serializer(model)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_serializer_with_args(faker):
    model_path = "tests.units.test_pydantic_celery.Example"
    model = {"foo": "bar", "pydantic_field": model_path}

    example_int = faker.pyint()
    example_str = faker.pystr()
    args = (example_int, example_str, model)

    assert (example_int, example_str, Example(foo="bar")) == serializer(args)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_serializer_with_kwargs(faker):
    model_path = "tests.units.test_pydantic_celery.Example"
    model = {"foo": "bar", "pydantic_field": model_path}

    example_int = faker.pyint()
    example_str = faker.pystr()
    kwargs = {"int": example_int, "str": example_str, "model": model}

    assert {
        "int": example_int,
        "str": example_str,
        "model": Example(foo="bar"),
    } == serializer(kwargs)


def test_deserializer_with_simple_value(faker):
    value = faker.pystr()
    assert value == deserializer(value)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_deserializer_with_pydantic_model():
    model = Example(foo="bar")
    assert {
        "foo": "bar",
        "pydantic_field": "tests.units.test_pydantic_celery.Example",
    } == deserializer(model)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_deserializer_with_args(faker):
    example_int = faker.pyint()
    example_str = faker.pystr()
    args = (example_int, example_str, Example(foo="bar"))

    assert (
        example_int,
        example_str,
        {"foo": "bar", "pydantic_field": "tests.units.test_pydantic_celery.Example"},
    ) == deserializer(args)


@mock.patch("app.secbot.schemas.PYDANTIC_CLS_PATH", new="pydantic_field")
def test_deserializer_with_kwargs(faker):
    example_int = faker.pyint()
    example_str = faker.pystr()
    kwargs = {"int": example_int, "str": example_str, "model": Example(foo="bar")}
    assert {
        "int": example_int,
        "str": example_str,
        "model": {
            "foo": "bar",
            "pydantic_field": "tests.units.test_pydantic_celery.Example",
        },
    } == deserializer(kwargs)
