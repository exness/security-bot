from hashlib import sha256
from pathlib import Path

import yarl

from app.secbot.inputs.gitlab.schemas import AnyGitlabModel, GitlabWebhookSecurityID
from app.settings import GitlabConfig, settings


def get_project_name(git_ssh_url: str) -> str:
    """Get project name from git ssh url."""
    project = git_ssh_url
    if project.startswith("git@"):
        project = project[4:]
    if project.endswith(".git"):
        project = project[:-4]
    return project


def generate_gitlab_security_id(
    prefix: str,
    data: AnyGitlabModel,
) -> GitlabWebhookSecurityID:
    """Generate hash of gitlab webhook event.

    The algorithm is a string with the formation of git prefix
    (since we have not only one GitLab)
    and sha256 of project path and complete commit hash.
    """
    project_path = get_project_name(data.project.git_ssh_url)
    hash_str = f"{project_path}_{data.commit.id}"
    return GitlabWebhookSecurityID(f"{prefix}_{sha256(hash_str.encode()).hexdigest()}")


def override_git_credentials():
    """Overrides Git credentials using configurations from the settings.

    This function creates/overwrites a '.git-credentials' file at the user's home directory.
    The file includes the hosts from GitLab configurations in the settings, each paired with
    an 'oauth2' user and a corresponding authentication token.

    Returns:
        A file object representing the '.git-credentials' file.

    Raises:
        Exception: Any exception that occurs while writing to the file.
    """
    user = "oauth2"
    git_credentials_path = Path.home() / ".git-credentials"
    git_credentials_file = open(git_credentials_path, "w")

    try:
        git_credentials_content = "\n".join(
            [
                str(
                    yarl.URL(config.host)
                    .with_user(user)
                    .with_password(config.auth_token.get_secret_value())
                )
                for config in settings.gitlab_configs
            ]
        )
        git_credentials_file.write(git_credentials_content)

        return git_credentials_file
    finally:
        git_credentials_file.close()


def get_config_from_host(host: str) -> GitlabConfig:
    """
    Retrieves a GitLab configuration that matches a specified host.

    This function iterates over all GitLab configurations in the settings. It returns
    the first configuration whose host matches the provided host string.

    Args:
        host (str): The host to match against GitLab configurations.

    Returns:
        GitlabConfig: The GitLab configuration that matches the provided host.

    Raises:
        StopIteration: If no configuration matches the provided host.
    """
    return next(
        config for config in settings.gitlab_configs if config.host.host == host
    )
