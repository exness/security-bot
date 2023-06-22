import abc
import enum
from datetime import datetime

from pydantic import AnyUrl, BaseModel

CommitHash = str


class Repository(BaseModel):
    name: str
    url: str
    homepage: AnyUrl


class Author(BaseModel):
    name: str
    email: str


class Project(BaseModel):
    id: int
    name: str
    web_url: AnyUrl
    git_ssh_url: str
    git_http_url: AnyUrl
    namespace: str
    path_with_namespace: str


class Commit(BaseModel):
    id: CommitHash
    message: str
    timestamp: datetime
    url: AnyUrl
    author: Author


class GitlabEvent(str, enum.Enum):
    PUSH = "Push Hook"
    TAG_PUSH = "Tag Push Hook"
    MERGE_REQUEST = "Merge Request Hook"


class BaseGitlabEventData(BaseModel, abc.ABC):
    project: Project
    repository: Repository
    raw: dict

    @property
    @abc.abstractmethod
    def target_branch(self) -> str:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def commit(self) -> Commit:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def path(self) -> str:
        raise NotImplementedError()

    @property
    def team_name(self) -> str:
        return self.repository.homepage.path[1:]
