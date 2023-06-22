from slack_sdk.web.async_client import AsyncWebClient


async def send_message(
    token: str,
    channel: str,
    payload: dict,
) -> None:
    """Send message payload to the specific channel via a secbot app."""
    assert token, "The token is missing."
    assert channel, "The channel name is missing."
    assert payload, "The payload can't be empty."

    client = AsyncWebClient(token=token)
    await client.chat_postMessage(channel=channel, blocks=payload)
