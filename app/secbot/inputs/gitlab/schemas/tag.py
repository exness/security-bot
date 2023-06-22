from typing import List

from app.secbot.inputs.gitlab.schemas.base import (
    BaseGitlabEventData,
    Commit,
    CommitHash,
)


class TagWebhookModel(BaseGitlabEventData):
    checkout_sha: CommitHash
    ref: str
    commits: List[Commit]

    @property
    def path(self) -> str:
        return self.commit.url

    @property
    def target_branch(self) -> str:
        assert "tags" in self.ref

        parts = self.ref.split("/")
        return parts[-1]

    @property
    def commit(self) -> Commit:
        return next(
            event_commit
            for event_commit in self.commits
            if event_commit.id == self.checkout_sha
        )
