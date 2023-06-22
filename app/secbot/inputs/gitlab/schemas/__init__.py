from __future__ import annotations

from typing import Any, Dict, List, NewType, Type, Union

from app.secbot.inputs.gitlab.schemas.base import GitlabEvent
from app.secbot.inputs.gitlab.schemas.merge_request import MergeRequestWebhookModel
from app.secbot.inputs.gitlab.schemas.output_responses import OutputResponse
from app.secbot.inputs.gitlab.schemas.push import PushWebhookModel
from app.secbot.inputs.gitlab.schemas.tag import TagWebhookModel
from app.secbot.schemas import SecbotBaseModel

# A generated hash string of GitLab event.
# To reference, look at the `generate_gitlab_security_id` method.
GitlabWebhookSecurityID = NewType("GitlabWebhookSecurityID", str)

# Common type for all GitLab models.
AnyGitlabModel = Union[MergeRequestWebhookModel, PushWebhookModel, TagWebhookModel]

# Map of GitLab events to models.
GITLAB_EVENTS_MAP: Dict[GitlabEvent, Type[AnyGitlabModel]] = {
    GitlabEvent.PUSH: PushWebhookModel,
    GitlabEvent.TAG_PUSH: TagWebhookModel,
    GitlabEvent.MERGE_REQUEST: MergeRequestWebhookModel,
}


def get_gitlab_model_for_event(event: GitlabEvent, data: dict) -> AnyGitlabModel:
    """Get the GitLab model for the given event."""
    model = GITLAB_EVENTS_MAP[event]
    return model(**data, raw=data)


class GitlabInputData(SecbotBaseModel):
    """Input model for GitLab events."""

    db_check_id: int
    event: GitlabEvent
    data: AnyGitlabModel


class GitlabScanResultFile(SecbotBaseModel):
    """Scan result file data for GitLab events."""

    commit_hash: str
    scan_name: str
    format: str
    content: Union[Dict[str, Any], List[Dict[str, Any]]]

    @property
    def filename(self) -> str:
        return f"{self.commit_hash}_gitlab_{self.scan_name}.{self.format}"


class GitlabScanResult(SecbotBaseModel):
    """Scan result model for GitLab events."""

    db_id: int
    handler_name: str
    component_name: str
    input: GitlabInputData
    file: GitlabScanResultFile


class GitlabOutputResult(SecbotBaseModel):
    """Output result model for GitLab events."""

    component_name: str
    handler_name: str
    scan_result: GitlabScanResult
    response: OutputResponse
