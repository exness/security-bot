from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.secbot.db import Base
from app.secbot.inputs.gitlab.schemas import GitlabEvent
from app.secbot.schemas import ScanStatus


class RepositorySecurityCheck(Base):
    """The base model of GitLab repository check.

    Each GitLab event should have only one RepositorySecurityCheck.
    """

    __tablename__ = "repository_security_check"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=False, unique=True)

    event_type = Column(Enum(GitlabEvent), nullable=False)
    event_json = Column(JSON, nullable=False)

    commit_hash = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    prefix = Column(String, nullable=False)

    scans = relationship("RepositorySecurityScan", lazy=True)


class RepositorySecurityScan(Base):
    """The base model of a particular service scan of repository security check.

    Each service should have only one scan within the one check.
    """

    __tablename__ = "repository_security_scan"

    check_id = Column(
        Integer,
        ForeignKey("repository_security_check.id"),
        nullable=False,
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    status = Column(Enum(ScanStatus), nullable=False, default=ScanStatus.NEW)
    response = Column(JSON, nullable=True)

    # Config name of the scan
    scan_name = Column(String, nullable=False)

    # Map to outputs and test id in third party services
    # e.g.
    # {"defectdojo": 42, "other": "test-123"}
    outputs_test_id = Column(JSON)

    slack_notification = relationship("SlackNotifications", lazy=True, uselist=False)


class SlackNotifications(Base):
    """State of scan notification to the Slack channel"""

    __tablename__ = "slack_notifications"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    channel = Column(String, nullable=False)
    is_sent = Column(Boolean, default=False)
    payload = Column(JSON, nullable=False)

    scan_id = Column(
        Integer,
        ForeignKey("repository_security_scan.id"),
        nullable=False,
    )
