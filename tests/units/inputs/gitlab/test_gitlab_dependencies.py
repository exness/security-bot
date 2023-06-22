from unittest import mock

import pytest
from fastapi import HTTPException

from app.secbot.inputs.gitlab.dependencies import (
    get_gitlab_webhook_token_header,
    gitlab_event,
)
from app.secbot.inputs.gitlab.schemas import GitlabEvent


@mock.patch("app.secbot.inputs.gitlab.dependencies.settings")
def test_gitlab_webhook_token_header(settings_mock, faker):
    token = faker.pystr()

    get_secret_value_mock = mock.Mock(get_secret_value=mock.Mock(return_value=token))
    settings_mock.gitlab_configs = [
        mock.Mock(webhook_secret_token=get_secret_value_mock),
    ]

    assert get_gitlab_webhook_token_header(x_gitlab_token=token) == token


@mock.patch("app.secbot.inputs.gitlab.dependencies.settings")
def test_gitlab_webhook_token_header_invalid(settings_mock):
    get_secret_value_mock = mock.Mock(get_secret_value=mock.Mock(return_value="valid"))
    settings_mock.gitlab_configs = [
        mock.Mock(webhook_secret_token=get_secret_value_mock),
    ]

    with pytest.raises(HTTPException):
        get_gitlab_webhook_token_header(x_gitlab_token="invalid")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_name, payload, expected_event",
    [
        (
            "System Hook",
            {"event_type": "merge_request"},
            GitlabEvent.MERGE_REQUEST,
        ),
        (
            "System Hook",
            {"event_name": "push"},
            GitlabEvent.PUSH,
        ),
        (
            "System Hook",
            {"event_name": "tag_push"},
            GitlabEvent.TAG_PUSH,
        ),
        (
            "Merge Request Hook",
            {"event_type": "merge_request"},
            GitlabEvent.MERGE_REQUEST,
        ),
        (
            "Push Hook",
            {"event_name": "push"},
            GitlabEvent.PUSH,
        ),
        (
            "Tag Push Hook",
            {"event_name": "tag_push"},
            GitlabEvent.TAG_PUSH,
        ),
    ],
)
async def test_gitlab_event_event_detection(event_name, payload, expected_event):
    request_mock = mock.Mock(json=mock.AsyncMock(return_value=payload))
    event = await gitlab_event(request_mock, x_gitlab_event=event_name)
    assert event == expected_event


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_name",
    [
        "System Hook",
        "Random event name",
    ],
)
async def test_gitlab_not_supported_event(event_name, faker):
    random_event_payload = faker.pydict()
    request_mock = mock.Mock(json=mock.AsyncMock(return_value=random_event_payload))
    event = await gitlab_event(request_mock, x_gitlab_event=event_name)
    assert event is None
