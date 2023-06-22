from unittest import mock

from app.secbot import SecurityBot
from app.secbot.inputs.gitlab import GitlabInput


def test_autodiscover_gitlab():
    celery_app = mock.Mock()
    runner = SecurityBot(celery_app=celery_app)

    assert "gitlab" in runner._registered_inputs


def test_gitlab_autodiscover_inputs():
    celery_app = mock.Mock()
    gitlab_input = GitlabInput(config_name="gitlab", celery_app=celery_app)

    assert "gitleaks" in gitlab_input.scans
    assert "defectdojo" in gitlab_input.outputs
    assert "slack" in gitlab_input.notifications
