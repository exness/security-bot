import json
import subprocess
import tempfile

from sqlalchemy import update

from app.secbot.db import db_session
from app.secbot.exceptions import ScanCheckFailed
from app.secbot.handlers import SecbotScanHandler
from app.secbot.inputs.gitlab import RepositorySecurityScan
from app.secbot.inputs.gitlab.schemas import (
    GitlabInputData,
    GitlabScanResult,
    GitlabScanResultFile,
)
from app.secbot.inputs.gitlab.services import (
    clone_repository,
    handle_exception,
    start_scan,
)
from app.secbot.schemas import SecbotBaseModel


class GitleaksConfig(SecbotBaseModel):
    format: str = "json"


class GitleaksHandler(SecbotScanHandler):
    config_model = GitleaksConfig

    async def on_failure(
        self,
        input_data: GitlabInputData,
        exception,
        component_name: str,
        config: GitleaksConfig,
    ) -> None:
        await handle_exception(
            check_id=input_data.db_check_id,
            scan_component_name=component_name,
            exception=exception,
        )

    async def run(
        self,
        input_data: GitlabInputData,
        component_name: str,
        config: GitleaksConfig,
    ) -> GitlabScanResult:
        # Create and start the gitleaks scan object
        scan = await start_scan(component_name, input_data.db_check_id)

        # Clone the entire repository and save it in the temporary directory
        with clone_repository(
            repository_url=input_data.data.project.git_http_url,
            reference=input_data.data.commit.id,
        ) as repository_temp_path:

            # Create a temporary file and save the result of the check in it
            with tempfile.NamedTemporaryFile(prefix="secbot-gitleaks-") as temp_file:
                try:
                    subprocess.run(
                        [
                            "gitleaks",
                            "detect",
                            "--redact",
                            "-f",
                            config.format,
                            "-r",
                            temp_file.name,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        cwd=repository_temp_path,
                        check=False,
                    )
                except RuntimeError:
                    raise ScanCheckFailed()

                # Read the content of the temporary file with scan defects
                # and save it in the database
                with open(temp_file.name, "rb") as output_file:
                    content = output_file.read()
                    response = json.loads(content.decode())

                    async with db_session() as session:
                        await session.execute(
                            update(RepositorySecurityScan)
                            .where(RepositorySecurityScan.id == scan.id)
                            .values(response=response)
                        )
                        await session.commit()

                scan_file = GitlabScanResultFile(
                    commit_hash=input_data.data.commit.id,
                    scan_name=self.config_name,
                    format=config.format,
                    content=response,
                )
                return GitlabScanResult(
                    db_id=scan.id,
                    input=input_data,
                    handler_name=self.config_name,
                    component_name=component_name,
                    file=scan_file,
                )
