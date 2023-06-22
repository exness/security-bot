import tempfile
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional, Union, cast
from urllib.parse import urlparse

import git
import requests
import yarl
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_scoped_session

from app.secbot.db import db_session as async_db_session
from app.secbot.exceptions import ScanCantBeScanned, ScanExecutionSkipped
from app.secbot.inputs.gitlab.models import (
    RepositorySecurityCheck,
    RepositorySecurityScan,
)
from app.secbot.inputs.gitlab.schemas import GitlabWebhookSecurityID
from app.secbot.inputs.gitlab.schemas.base import Project
from app.secbot.inputs.gitlab.utils import get_config_from_host
from app.secbot.logger import logger
from app.secbot.schemas import ScanStatus


@contextmanager
def clone_repository(
    repository_url: str,
    reference: str = "main",
):
    """
    Clone a Git repository to a temporary directory and checkout to a specific reference.

    This context manager clones a Git repository specified by its URL into a temporary
    directory, checks out to a certain reference (default to 'main'), and then cleans
    up the directory once done.

    Args:
        repository_url (str): The URL of the Git repository to clone.
        reference (str, optional): The Git reference to checkout. Defaults to 'main'.

    Yields:
        str: The path to the temporary directory where the repository was cloned.

    Raises:
        AssertionError: If the hostname can't be parsed from the repository URL.
    """
    host = urlparse(repository_url).hostname
    assert host

    with tempfile.TemporaryDirectory() as temp_directory:
        user = "oauth2"
        token = get_config_from_host(host).auth_token.get_secret_value()

        repository_url = str(
            yarl.URL(repository_url).with_user(user).with_password(token)
        )
        repo = git.Repo.clone_from(repository_url, temp_directory)
        repo.git.checkout(reference)
        yield temp_directory


def get_gitlab_project_languages(project: Project) -> Optional[Dict[str, float]]:
    """
    Returns the dictionary with languages for the project or None if it was not possible to get it
    Example dict: {'Python': 75.06, 'Makefile': 11.11, 'Dockerfile': 7.95, 'Shell': 5.87}
    """
    host = urlparse(project.web_url).hostname
    assert host

    token = get_config_from_host(host).auth_token.get_secret_value()
    api_url = yarl.URL(project.web_url).with_path(
        f"/api/v4/projects/{project.id}/languages"
    )
    # TODO(ivan.zhirov): make it async
    response = requests.get(
        url=str(api_url),
        headers={"PRIVATE-TOKEN": token},
    )
    if response.status_code != 200:
        return None
    return cast(Dict[str, float], response.json())


# TODO(ivan.zhirov): add tests
async def get_or_create_security_check(
    db_session: async_scoped_session,
    external_id: GitlabWebhookSecurityID,
    initial_data: Optional[dict] = None,
) -> RepositorySecurityCheck:
    """Retrieve or create a new RepositorySecurityCheck entry.

    Args:
        db_session (async_scoped_session): The database session to use for the operation.
        external_id (GitlabWebhookSecurityID): The external ID to search for.
        initial_data (Optional[dict], optional): The data to use if creating a new entry.
            Defaults to None, in which case an empty dict is used.

    Returns:
        RepositorySecurityCheck: The retrieved or newly created RepositorySecurityCheck entry.
    """

    async def get_security_check() -> RepositorySecurityCheck:
        return (
            await db_session.execute(
                select(RepositorySecurityCheck).where(
                    RepositorySecurityCheck.external_id == external_id,
                )
            )
        ).scalar()

    security_check = await get_security_check()
    try:
        if not security_check:
            initial_data = initial_data or {}
            security_check = RepositorySecurityCheck(
                external_id=external_id,
                **initial_data,
            )
            db_session.add(security_check)
            await db_session.commit()
    except IntegrityError:
        security_check = await get_security_check()
    return security_check


# TODO(ivan.zhirov): add tests
async def get_or_create_security_scan(
    db_session: async_scoped_session,
    check_id: int,
    scan_name: str,
) -> RepositorySecurityScan:
    """Retrieve or create a new RepositorySecurityScan entry.

    Args:
        db_session (async_scoped_session): The database session to use for the operation.
        check_id (int): The check ID to search for.
        scan_name (str): The scan name to search for.

    Returns:
        RepositorySecurityScan: The retrieved or newly created RepositorySecurityScan entry.
    """

    async def get_scan() -> RepositorySecurityScan:
        return (
            await db_session.execute(
                select(RepositorySecurityScan).where(
                    and_(
                        RepositorySecurityScan.check_id == check_id,
                        RepositorySecurityScan.scan_name == scan_name,
                    )
                )
            )
        ).scalar()

    scan = await get_scan()
    try:
        if not scan:
            scan = RepositorySecurityScan(
                check_id=check_id,
                scan_name=scan_name,
            )
            db_session.add(scan)
            await db_session.commit()
    except IntegrityError:
        scan = await get_scan()
    return scan


async def start_scan(scan_name: str, check_id: int) -> RepositorySecurityScan:
    """Initiate a security scan and update its status to 'IN_PROGRESS'.

    This asynchronous function starts a security scan by first fetching or creating
    a RepositorySecurityScan entry via the get_or_create_security_scan() function.
    It then checks the current status of the scan. If the status is neither 'NEW' nor
    'ERROR', an exception (ScanCantBeScanned) is raised, preventing the scan from starting.
    If the status is either 'NEW' or 'ERROR', the function updates the status of the scan
    to 'IN_PROGRESS', sets the start time to the current datetime, commits these changes
    to the database, and finally returns the RepositorySecurityScan entry.

    Args:
        scan_name (str): The name of the scan.
        check_id (int): The ID of the check for the scan.

    Returns:
        RepositorySecurityScan: The updated RepositorySecurityScan entry.

    Raises:
        ScanCantBeScanned: If the status of the scan is not 'NEW' or 'ERROR'.
    """
    async with async_db_session() as session:
        scan = await get_or_create_security_scan(
            db_session=session,
            check_id=check_id,
            scan_name=scan_name,
        )
        if scan.status not in [ScanStatus.NEW, ScanStatus.ERROR]:
            raise ScanCantBeScanned(
                f"Scan can't be scanned: reason={scan.status}",
                scan.id,
            )

        # Update the scan status to In progress
        scan.status = ScanStatus.IN_PROGRESS
        scan.started_at = datetime.now()

        session.add(scan)
        await session.commit()

        return scan


async def complete_scan(
    *,
    scan_id: int,
    output_component_name: str,
    output_external_test_id: Union[str, int],
):
    """Mark a security scan as complete and update related information.

    This function is used to mark a specific security scan as completed (DONE).
    It first retrieves the specific RepositorySecurityScan instance from the
    database using the provided scan_id. It then updates the scan's
    'outputs_test_id' field by appending the output_external_test_id associated
    with the output_component_name. The scan status is then set to 'DONE', and the
    completion time is recorded as the current datetime. These updates are then
    committed to the database.

    Args:
        scan_id (int): The ID of the scan to be completed.
        output_component_name (str): The name of the output component related to the scan.
        output_external_test_id (Union[str, int]): The external test ID related to the output component.

    Raises:
        AssertionError: If the scan with the provided scan_id does not exist.
    """

    async with async_db_session() as session:
        scan = (
            await session.execute(
                select(RepositorySecurityScan).where(
                    RepositorySecurityScan.id == scan_id
                )
            )
        ).scalar()
        assert scan is not None, "Scan id is not defined"

        scan.outputs_test_id = {
            **(scan.outputs_test_id or {}),
            output_component_name: output_external_test_id,
        }
        scan.status = ScanStatus.DONE
        scan.finished_at = datetime.now()
        await session.commit()


async def handle_exception(
    *,
    check_id: int,
    scan_component_name: str,
    exception: Exception,
):
    """Handle an exception that occurred during a security scan.

    This asynchronous function is designed to handle exceptions that occur
    during a security check. It updates the status of the current scan in the database
    according to the type of exception that occurred. If the scan cannot be found,
    it logs a warning and re-raises the exception.

    If the exception is of type ScanExecutionSkipped, the scan status is updated to 'SKIP'.
    For any other type of exception, the scan status is set to 'ERROR'.

    Args:
        check_id (int): The ID of the security check associated with the scan.
        scan_component_name (str): The name of the scan component where the exception occurred.
        exception (Exception): The exception that occurred.

    Raises:
        Exception: If the scan associated with the provided
        check_id and scan_component_name does not exist in the database,
        the function re-raises the passed exception.
    """
    async with async_db_session() as session:
        # Getting the current handler scan
        scan = (
            await session.execute(
                select(RepositorySecurityScan).where(
                    and_(
                        RepositorySecurityScan.check_id == check_id,
                        RepositorySecurityScan.scan_name == scan_component_name,
                    )
                )
            )
        ).scalar()

        # In case we failed even before the scan has been created
        # We just log the error and re-raise the exception
        if not scan:
            logger.warning("Scan id is not defined")
            raise exception

        if isinstance(exception, ScanExecutionSkipped):
            # We mark the scan as skipped in order that scan has been failed
            # but in good way (e.g. we don't support the language).
            # Later, the scan will be not be used in result checks.
            scan.status = ScanStatus.SKIP
        else:
            scan.status = ScanStatus.ERROR
        await session.commit()
