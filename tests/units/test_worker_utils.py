from unittest.mock import patch

from app.secbot.inputs.gitlab.services import get_gitlab_project_languages
from tests.units import factories


@patch("app.secbot.inputs.gitlab.services.requests")
@patch("app.secbot.inputs.gitlab.services.get_config_from_host")
def test_gitlab_language(_config_mock, requests_mock):
    project = factories.create_project__security()
    requests_mock.get.return_value.status_code = 200
    requests_mock.get.return_value.json.return_value = {
        "Python": 52.01,
        "Javascript": 47.98,
        "Go": 0.01,
    }
    languages = get_gitlab_project_languages(project)

    requests_mock.get.assert_called_once()
    assert len(languages.keys()) >= 3
    assert "Python" in languages.keys()
    assert languages["Python"] > 50.0
