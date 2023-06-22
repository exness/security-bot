from unittest import mock

import pytest

from app.secbot.config import SecbotConfig
from app.secbot.exceptions import SecbotConfigError


def test_missing_version_key():
    config_obj = {"components": {}, "jobs": []}
    with pytest.raises(SecbotConfigError):
        SecbotConfig(config_obj)


def test_unsupported_version():
    config_obj = {"version": "invalid_version", "components": {}, "jobs": []}
    with pytest.raises(SecbotConfigError):
        SecbotConfig(config_obj)


def test_valid_config():
    version = "1.0"
    mock_parser = mock.MagicMock()
    with mock.patch.dict(SecbotConfig.VERSIONS_PARSER, {version: mock_parser}):
        config_obj = {"version": version, "components": {}, "jobs": []}
        SecbotConfig(config_obj)
        mock_parser.assert_called_once_with(config_obj)
