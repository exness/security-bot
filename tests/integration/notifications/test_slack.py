from unittest import mock

import pytest

from app.secbot.inputs.gitlab.handlers.slack import send_message


@pytest.mark.asyncio
@mock.patch(
    "app.secbot.inputs.gitlab.handlers.slack.api.AsyncWebClient", new=mock.AsyncMock
)
async def test_sending_message_without_token(faker):
    channel = faker.pystr()
    payload = faker.pydict()
    token = None

    with pytest.raises(AssertionError):
        await send_message(channel=channel, payload=payload, token=token)


@pytest.mark.asyncio
@mock.patch(
    "app.secbot.inputs.gitlab.handlers.slack.api.AsyncWebClient", new=mock.AsyncMock
)
async def test_sending_message_without_channel(faker):
    channel = None
    payload = faker.pydict()
    token_value = faker.pystr()
    token = mock.Mock(get_secret_value=mock.Mock(return_value=token_value))

    with pytest.raises(AssertionError):
        await send_message(channel=channel, payload=payload, token=token)


@pytest.mark.asyncio
@mock.patch(
    "app.secbot.inputs.gitlab.handlers.slack.api.AsyncWebClient", new=mock.AsyncMock
)
async def test_sending_message_without_payload(faker):
    channel = faker.pystr()
    payload = None
    token_value = faker.pystr()
    token = mock.Mock(get_secret_value=mock.Mock(return_value=token_value))

    with pytest.raises(AssertionError):
        await send_message(channel=channel, payload=payload, token=token)


@pytest.mark.asyncio
@mock.patch(
    "app.secbot.inputs.gitlab.handlers.slack.api.AsyncWebClient.chat_postMessage"
)
async def test_sending_message(post_message_mock, faker):
    channel = faker.pystr()
    payload = faker.pydict()
    token_value = faker.pystr()
    token = mock.Mock(get_secret_value=mock.Mock(return_value=token_value))

    await send_message(channel=channel, payload=payload, token=token)

    post_message_mock.assert_called_once_with(
        channel=channel,
        blocks=payload,
    )
