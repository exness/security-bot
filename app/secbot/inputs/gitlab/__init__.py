from sqlalchemy import select

from app.secbot.config import config
from app.secbot.db import db_session
from app.secbot.inputs import SecbotInput
from app.secbot.inputs.gitlab.models import (
    RepositorySecurityCheck,
    RepositorySecurityScan,
)
from app.secbot.inputs.gitlab.schemas import (
    AnyGitlabModel,
    GitlabEvent,
    GitlabInputData,
    GitlabWebhookSecurityID,
)
from app.secbot.inputs.gitlab.services import get_or_create_security_check
from app.secbot.inputs.gitlab.utils import (
    generate_gitlab_security_id,
    get_config_from_host,
)
from app.secbot.logger import logger
from app.secbot.schemas import ScanStatus, SecurityCheckStatus


# noinspection PyMethodOverriding
class GitlabInput(SecbotInput):
    async def run(
        self,
        data: AnyGitlabModel,
        event: GitlabEvent,
    ):
        job = config.matching_workflow_job("gitlab", data.raw)
        if not job:
            logger.info(f"No matching workflow job for {event}")
            return

        gitlab_config = get_config_from_host(data.repository.homepage.host)
        security_id = generate_gitlab_security_id(gitlab_config.prefix, data=data)

        async with db_session() as session:
            check = await get_or_create_security_check(
                db_session=session,
                external_id=security_id,
                initial_data={
                    "event_type": event,
                    "event_json": data.raw,
                    "commit_hash": data.commit.id,
                    "branch": data.target_branch,
                    "project_name": data.repository.name,
                    "path": data.repository.homepage,
                    "prefix": gitlab_config.prefix,
                },
            )
            input_data = GitlabInputData(
                event=check.event_type,
                data=data,
                db_check_id=check.id,
            )
        return await super().run(input_data, job=job)

    async def fetch_status(
        self, security_check_id: GitlabWebhookSecurityID
    ) -> SecurityCheckStatus:
        async with db_session() as session:
            check = (
                await session.execute(
                    select(RepositorySecurityCheck).where(
                        RepositorySecurityCheck.external_id == security_check_id
                    )
                )
            ).scalar()
            if not check:
                return SecurityCheckStatus.NOT_STARTED

            scans = (
                await session.execute(
                    select(
                        [
                            RepositorySecurityScan.status,
                            RepositorySecurityScan.scan_name,
                            RepositorySecurityScan.outputs_test_id,
                        ]
                    ).where(RepositorySecurityScan.check_id == check.id)
                )
            ).all()

            # Define if we have enough scans
            # we suppose that we have only one job for a security check
            job = config.matching_workflow_job("gitlab", check.event_json)
            has_enough_scans = len(scans) == len(job.scans)

            # If we have not enough scans, we should wait for them
            if not has_enough_scans:
                return SecurityCheckStatus.IN_PROGRESS

            # If for some reason we have more scans than jobs
            if len(scans) > len(job.scans):
                return SecurityCheckStatus.ERROR

            # Remove skipped scans from checks
            scans = [scan for scan in scans if scan.status is not ScanStatus.SKIP]
            statuses = [scan.status for scan in scans if scan]

            if ScanStatus.ERROR in statuses:
                return SecurityCheckStatus.ERROR
            elif ScanStatus.IN_PROGRESS in statuses:
                return SecurityCheckStatus.IN_PROGRESS

            if all(status == ScanStatus.DONE for status in statuses):
                scan_outputs = set(
                    output_name
                    for scan in scans
                    for output_name in scan.outputs_test_id.keys()
                )
                outputs = [
                    output for output in job.outputs if output.name in scan_outputs
                ]
                scan_names = set(scan.scan_name for scan in scans)
                eligible_scans = [
                    scan for scan in job.scans if scan.name in scan_names
                ]
                return await super().fetch_status(
                    outputs,
                    eligible_scans=eligible_scans,
                    commit_hash=check.commit_hash,
                )
            return SecurityCheckStatus.ERROR
