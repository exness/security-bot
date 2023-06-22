import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.secbot.inputs.gitlab.schemas import GitlabWebhookSecurityID
from app.secbot.schemas import SecurityCheckStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/security", tags=["security"])


class SecurityCheckResponse(BaseModel):
    status: SecurityCheckStatus


# TODO(ivan.zhirov): add tests
@router.get(
    "/gitlab/check/{security_check_id}",
    response_model=SecurityCheckResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "examples": {
                        "Check happens before check has been created.": {
                            "value": {"status": "not_started"},
                        },
                        "Check happens before scans has been created.": {
                            "value": {"status": "not_started"},
                        },
                        "Technical problem with the scan": {
                            "value": {"status": "error"},
                        },
                        "Security check in progress": {
                            "value": {"status": "in_progress"},
                        },
                        "Security check has been failed": {
                            "value": {"status": "fail"},
                        },
                        "Security check has been successful": {
                            "value": {"status": "success"},
                        },
                    }
                }
            }
        }
    },
)
async def get_security_check(
    security_check_id: GitlabWebhookSecurityID,
) -> SecurityCheckResponse:
    from app.main import security_bot

    status = await security_bot.fetch_check_result("gitlab", security_check_id)
    return SecurityCheckResponse(status=status)
