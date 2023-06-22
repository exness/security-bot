from unittest import mock

import pytest

from app.secbot.config import SecbotConfigComponent, WorkflowJob, config_parser
from app.secbot.exceptions import SecbotConfigError, SecbotConfigMissingEnv


def test_config_v1_parser_empty_components():
    with pytest.raises(SecbotConfigError):
        config_parser({"version": "1.0", "components": {}, "jobs": []})


def test_config_v1_parser_empty_jobs():
    with pytest.raises(SecbotConfigError):
        config_parser(
            {
                "version": "1.0",
                "components": {
                    "component": {
                        "handler_name": "handler",
                        "config": {"key": "value"},
                    },
                },
                "jobs": [],
            }
        )


@mock.patch("app.secbot.config.os.getenv")
def test_config_v1_parser_missing_env(getenv_mock):
    getenv_mock.side_effect = AttributeError
    with pytest.raises(SecbotConfigMissingEnv):
        config_parser(
            {
                "version": "1.0",
                "components": {
                    "component": {
                        "handler_name": "handler",
                        "env": {
                            "key1": "value1",
                        },
                    },
                },
                "jobs": [
                    {
                        "name": "job1",
                        "rules": {"input": {"some": "rule"}},
                        "scans": ["component"],
                        "outputs": ["component"],
                        "notifications": [],
                    }
                ],
            }
        )


@mock.patch("app.secbot.config.os.getenv")
def test_config_v1_parser(getenv, faker):
    example_env_value = faker.pystr()
    getenv.return_value = example_env_value

    handler_1_name = faker.pystr()
    handler_2_name = faker.pystr()
    config_2 = faker.pydict()
    input_name = faker.pystr()

    obj = {
        "version": "1.0",
        "components": {
            "component1": {
                "handler_name": handler_1_name,
                "env": {"key": "value"},
            },
            "component2": {
                "handler_name": handler_2_name,
                "config": config_2,
            },
        },
        "jobs": [
            {
                "name": "job1",
                "rules": {input_name: {"some": "rule"}},
                "scans": ["component1"],
                "outputs": ["component2"],
                "notifications": [],
            },
            {
                "name": "job2",
                "rules": {input_name: {"some": "rule"}},
                "scans": ["component2"],
                "outputs": ["component1"],
                "notifications": [],
            },
        ],
    }
    result = config_parser(obj)

    # Check that getenv was called
    getenv.assert_called_once_with("value")

    assert input_name in result
    assert len(result[input_name]) == 2

    assert all(isinstance(item, WorkflowJob) for item in result[input_name])

    assert result[input_name][0].name == "job1"
    assert result[input_name][1].name == "job2"

    assert result[input_name][0].scans == [
        SecbotConfigComponent(
            handler_name=handler_1_name,
            name="component1",
            config=None,
            env={"key": example_env_value},
        )
    ]
    assert result[input_name][0].outputs == [
        SecbotConfigComponent(
            handler_name=handler_2_name,
            name="component2",
            config=config_2,
            env=None,
        )
    ]

    assert result[input_name][1].scans == [
        SecbotConfigComponent(
            handler_name=handler_2_name,
            name="component2",
            config=config_2,
            env=None,
        )
    ]
    assert result[input_name][1].outputs == [
        SecbotConfigComponent(
            handler_name=handler_1_name,
            name="component1",
            config=None,
            env={"key": example_env_value},
        )
    ]
