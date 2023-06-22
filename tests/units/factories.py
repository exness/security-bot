import json

from app.secbot.inputs.gitlab.schemas import MergeRequestWebhookModel
from app.secbot.inputs.gitlab.schemas.base import Project
from tests.units.common import get_test_root_directory


def create_project__example():
    project = Project(
        id=4809,
        name="Example Project",
        web_url="https://git.env.local/security/example-project/",
        git_ssh_url="git@git.env.local:security/example-project.git",
        git_http_url="https://git.env.local/security/example-project.git",
        namespace="security",
        path_with_namespace="security/example-project",
    )
    return project


def create_project__security():
    project = Project(
        id=4801,
        name="Security Bot",
        web_url="https://git.env.local/security/security-bot/",
        git_ssh_url="git@git.env.local:security/security-bot.git",
        git_http_url="https://git.env.local/security/security-bot.git",
        namespace="security",
        path_with_namespace="security/security-bot",
    )
    return project


def create_project__public_site():
    project = Project(
        id=164,
        name="Public Site",
        web_url="https://git.env.local/public-site/backend/",
        git_ssh_url="git@git.env.local:public-site/backend.git",
        git_http_url="https://git.env.local/public-site/backend.git",
        namespace="public-site",
        path_with_namespace="public-site/backend",
    )
    return project


def create_merge_request_webhook__example_project():
    with open(
        get_test_root_directory()
        / "fixtures"
        / "merge_request_hook__example_project.json"
    ) as json_data:
        return MergeRequestWebhookModel(**json.load(json_data), raw={})


def create_merge_request_webhook__security_bot():
    with open(
        get_test_root_directory()
        / "fixtures"
        / "merge_request_hook__security_bot.json"
    ) as json_data:
        return MergeRequestWebhookModel(**json.load(json_data), raw={})


def create_merge_request_webhook__public_site():
    with open(
        get_test_root_directory() / "fixtures" / "merge_request_hook__public_site.json"
    ) as json_data:
        return MergeRequestWebhookModel(**json.load(json_data), raw={})
