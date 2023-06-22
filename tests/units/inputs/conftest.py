import json
import pathlib
from typing import Dict, Optional

import pytest
from pydantic.utils import deep_update

from app.secbot.inputs.gitlab.schemas import GitlabEvent

GITLAB_EVENT_RESPONSE_MAP: Dict[GitlabEvent, str] = {
    GitlabEvent.MERGE_REQUEST: "fixtures/inputs/gitlab/merge_request_webhook.json",
    GitlabEvent.PUSH: "fixtures/inputs/gitlab/push_webhook.json",
    GitlabEvent.TAG_PUSH: "fixtures/inputs/gitlab/tag_push_webhook.json",
}


@pytest.fixture
def get_event_data(dir_tests):
    def handler(event: GitlabEvent, overrides: Optional[dict] = None) -> dict:
        file_path = GITLAB_EVENT_RESPONSE_MAP[event]
        with open(pathlib.Path(dir_tests, file_path), "r") as file:
            data = json.loads(file.read())
        data = deep_update(data, overrides or {})
        data["raw"] = data
        return data

    return handler


@pytest.fixture
def generate_commit_data(faker):
    def handler(overrides: Optional[dict] = None) -> dict:
        data = {
            "id": faker.md5(),
            "message": faker.pystr(),
            "title": faker.pystr(),
            "timestamp": faker.iso8601(),
            "url": faker.uri(),
            "author": {"name": faker.name(), "email": faker.ascii_email()},
            "added": [],
            "modified": [],
            "removed": [],
        }
        return deep_update(data, overrides or {})

    return handler
