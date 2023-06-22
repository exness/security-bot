from typing import List

from app.secbot.inputs.gitlab.schemas.base import (
    BaseGitlabEventData,
    Commit,
    CommitHash,
)


class PushWebhookModel(BaseGitlabEventData):
    after: CommitHash
    ref: str
    commits: List[Commit]

    @property
    def path(self) -> str:
        return self.commit.url

    @property
    def target_branch(self) -> str:
        assert "heads" in self.ref

        parts = self.ref.split("/")
        return parts[-1]

    @property
    def commit(self) -> Commit:
        return next(commit for commit in self.commits if commit.id == self.after)
