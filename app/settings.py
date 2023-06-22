from __future__ import annotations

import os.path
import pathlib
from typing import List, Optional, Set, Union

from pydantic import AnyUrl, BaseModel, BaseSettings, SecretStr

BASE_PATH = pathlib.Path(os.path.dirname(__file__))


def flatten_settings_values(app_settings: Settings) -> Set[Union[str, int]]:
    """Flattering all values from settings recursively."""

    def values(data):
        if hasattr(data, "dict"):
            return [values(value) for value in data.dict().values()]
        elif isinstance(data, dict):
            return [values(value) for value in data.values()]
        elif isinstance(data, list):
            return [values(item) for item in data]
        elif isinstance(data, SecretStr):
            return data.get_secret_value()
        elif isinstance(data, object):
            return str(data)
        return data

    def flatten(arg):
        if not isinstance(arg, list):
            return [arg]
        return [x for sub in arg for x in flatten(sub)]

    settings_values = flatten(values(app_settings))
    return set(settings_values)


class GitlabConfig(BaseModel):
    host: AnyUrl
    webhook_secret_token: SecretStr
    auth_token: SecretStr
    prefix: str


class Settings(BaseSettings):
    app_id: str = "security-bot"
    app_name: str = "Security Bot"
    app_host: str = "localhost"
    app_port: int = 5000

    debug: bool = False
    docs_enable: bool = True

    # Inputs
    gitlab_configs: List[GitlabConfig]

    # URLS
    sentry_dsn: Optional[AnyUrl] = None
    celery_broker_url: AnyUrl = "redis://redis:6379"
    celery_result_backend: AnyUrl = "redis://redis:6379"

    class Config:
        # Use this delimiter to split env variables
        # e.g.
        # DEFECTDOJO__URL=123 -> {"defectdojo": {"url": "123"}}
        env_nested_delimiter = "__"


settings = Settings()
