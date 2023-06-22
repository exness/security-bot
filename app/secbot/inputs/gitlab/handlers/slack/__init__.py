from typing import List

from sqlalchemy import select

from app.secbot.db import db_session
from app.secbot.handlers import SecbotNotificationHandler
from app.secbot.inputs.gitlab.handlers.slack.api import send_message
from app.secbot.inputs.gitlab.handlers.slack.utils import generate_message_blocks
from app.secbot.inputs.gitlab.models import SlackNotifications
from app.secbot.inputs.gitlab.schemas import GitlabOutputResult
from app.secbot.inputs.gitlab.services import handle_exception
from app.secbot.schemas import SecbotBaseModel


class SlackCredentials(SecbotBaseModel):
    token: str


class SlackConfig(SecbotBaseModel):
    render_limit: int
    channels: List[str]


class SlackHandler(SecbotNotificationHandler):
    config_name = "slack"
    config_model = SlackConfig
    env_model = SlackCredentials

    async def on_failure(
        self,
        output: GitlabOutputResult,
        exception,
        component_name: str,
        config: SlackConfig,
        env: SlackCredentials,
    ):
        await handle_exception(
            check_id=output.scan_result.input.db_check_id,
            scan_component_name=output.scan_result.component_name,
            exception=exception,
        )

    async def run(
        self,
        output: GitlabOutputResult,
        component_name: str,
        config: SlackConfig,
        env: SlackCredentials,
    ):
        """Send notification to slack channel."""
        message_blocks = generate_message_blocks(
            output=output,
            render_limit=config.render_limit,
        )
        if not message_blocks:
            return

        for channel in config.channels:
            async with db_session() as session:
                notification = (
                    await session.execute(
                        select(SlackNotifications)
                        .with_for_update()
                        .where(
                            SlackNotifications.scan_id == output.scan_result.db_id,
                            SlackNotifications.channel == channel,
                        )
                    )
                ).scalar()
                if notification and notification.is_sent is True:
                    return
                if not notification:
                    notification = SlackNotifications(
                        scan_id=output.scan_result.db_id,
                        channel=channel,
                        payload=message_blocks,
                    )
                await send_message(
                    channel=channel,
                    payload=notification.payload,
                    token=env.token,
                )
                notification.is_sent = True
                session.add(notification)
                await session.commit()
