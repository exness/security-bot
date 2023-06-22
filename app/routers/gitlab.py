import logging
from typing import Optional

import sentry_sdk
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.exceptions.schemas import ValidationError
from app.secbot.inputs.gitlab.dependencies import (
    get_gitlab_webhook_token_header,
    gitlab_event,
    webhook_model,
)
from app.secbot.inputs.gitlab.schemas import AnyGitlabModel, GitlabEvent

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/gitlab",
    tags=["gitlab"],
    dependencies=[Depends(get_gitlab_webhook_token_header)],
)


class WebhookReplyModel(BaseModel):
    status: str = "ok"


@router.post(
    "/webhook",
    response_model=WebhookReplyModel,
    response_description=f"""We support only {', '.join(GitlabEvent)} events.
     For the rest any events we will return 200 OK and do nothing.
    """,
    responses={
        403: {
            "description": "Gitlab webhook secret token missing or invalid",
            "model": ValidationError,
            "content": {
                "application/json": {
                    "example": {
                        "code": "FORBIDDEN",
                        "message": "X-Gitlab-Token header is invalid",
                        "details": None,
                    }
                },
            },
        },
    },
)
async def post_webhook(
    event: Optional[GitlabEvent] = Depends(gitlab_event),
    data: Optional[AnyGitlabModel] = Depends(webhook_model),
):
    if not event:
        logger.info("Unsupported event", extra={"event": event})
        return WebhookReplyModel()

    if not data:
        logger.warning("Unsupported event data", extra={"data": data})
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("event", event)
            scope.set_extra("data", data)
            sentry_sdk.capture_message("Unsupported event data")
        return WebhookReplyModel()

    logger.info(
        "Received gitlab webhook event",
        extra={"event": event, "data": data.raw},
    )
    from app.main import security_bot

    await security_bot.run("gitlab", data=data, event=event)
    return WebhookReplyModel()
