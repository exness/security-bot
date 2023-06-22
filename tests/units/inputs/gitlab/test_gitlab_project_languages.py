from unittest import mock

import pytest

from app.secbot.inputs.gitlab.schemas.base import Project
from app.secbot.inputs.gitlab.services import get_gitlab_project_languages


@pytest.fixture
def project_factory():
    def _factory(
        project_id: int = 42,
        web_url: str = "https://git.env.local/secbot-test-group/example-project",
    ):
        return Project(
            id=project_id,
            name="test",
            web_url=web_url,
            git_ssh_url="ssh://git.env.local/secbot-test-group/example-project",
            git_http_url="https://git.env.local/secbot-test-group/example-project",
            namespace="secbot-test-group",
            path_with_namespace="secbot-test-group/example-project",
        )

    return _factory


@mock.patch("app.secbot.inputs.gitlab.services.requests.get")
@mock.patch("app.secbot.inputs.gitlab.services.get_config_from_host")
def test_gitlab_project_languages_api_url(
    config_mock, requests_mock, faker, project_factory
):
    token = faker.pystr()
    project_id = faker.pyint()
    web_url = "https://git.env.local/secbot-test-group/example-project"
    project = project_factory(web_url=web_url, project_id=project_id)

    config_mock.return_value.auth_token.get_secret_value.return_value = token

    get_gitlab_project_languages(project)

    requests_mock.assert_called_once_with(
        url=f"https://git.env.local/api/v4/projects/{project_id}/languages",
        headers={"PRIVATE-TOKEN": token},
    )


@mock.patch(
    "app.secbot.inputs.gitlab.services.requests.get",
    return_value=mock.Mock(
        status_code=400,
        json=mock.MagicMock(return_value={"message": "error message"}),
    ),
)
@mock.patch("app.secbot.inputs.gitlab.services.get_config_from_host")
def test_gitlab_project_languages_non_success(_config_mock, _mock, project_factory):
    project = project_factory()
    assert get_gitlab_project_languages(project) is None


@mock.patch(
    "app.secbot.inputs.gitlab.services.requests.get",
    return_value=mock.Mock(
        status_code=200,
        json=mock.MagicMock(return_value={"Python": "90.00", "Shell": "10.00"}),
    ),
)
@mock.patch("app.secbot.inputs.gitlab.services.get_config_from_host")
def test_gitlab_project_languages_success_response(
    _config_mock, _mock, project_factory
):
    project = project_factory()
    assert get_gitlab_project_languages(project) == {
        "Python": "90.00",
        "Shell": "10.00",
    }
