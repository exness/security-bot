from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import AnyUrl, BaseModel

from app.secbot.inputs.gitlab.schemas.base import BaseGitlabEventData, Commit


class MergeRequestAction(str, Enum):
    open = "open"
    close = "close"
    reopen = "reopen"
    update = "update"
    approved = "approved"
    unapproved = "unapproved"
    merge = "merge"


class MergeRequestObjectAttributes(BaseModel):
    id: int
    url: AnyUrl
    state: str
    target_branch: str
    source_branch: str
    action: Optional[MergeRequestAction]
    last_commit: Commit


class MergeRequestWebhookModel(BaseGitlabEventData):
    object_attributes: MergeRequestObjectAttributes

    @property
    def commit(self) -> Commit:
        return self.object_attributes.last_commit

    @property
    def path(self) -> str:
        return self.object_attributes.url

    @property
    def target_branch(self) -> str:
        return self.object_attributes.target_branch
