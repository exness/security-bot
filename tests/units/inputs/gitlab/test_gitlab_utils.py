from unittest import mock

import pytest

from app.secbot.inputs.gitlab import generate_gitlab_security_id
from app.secbot.inputs.gitlab.utils import get_project_name


@pytest.mark.parametrize(
    "project_path, expected_project_name",
    [
        (
            "git.env.local:sample-group/sample-project.git",
            "git.env.local:sample-group/sample-project",
        ),
        (
            "git@git.env.local:sample-group/sample-project",
            "git.env.local:sample-group/sample-project",
        ),
    ],
)
def test_get_project_name_with_git_at_the_end(project_path, expected_project_name):
    assert get_project_name(project_path) == expected_project_name


def test_get_project_name_with_plain_string(faker):
    simple_string = faker.pystr()
    project_name = get_project_name(simple_string)
    assert simple_string == project_name


# noinspection SpellCheckingInspection
def test_generate_gitlab_security_id():
    prefix = "prefix"
    commit_hash = "commit_hash"
    project_path = "git.env.local:sample-group/sample-project.git"

    data = mock.Mock(
        commit=mock.Mock(id=commit_hash),
        project=mock.Mock(git_ssh_url=project_path),
    )
    security_id = generate_gitlab_security_id(prefix=prefix, data=data)
    assert (
        security_id
        == "prefix_8666e7b2f4a9023e9049d3e1dcc6012c8ede0351562876d482fa89d07a66f6f0"
    )
