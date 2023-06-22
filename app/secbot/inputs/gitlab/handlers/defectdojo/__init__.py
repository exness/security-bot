import json
from typing import List

from pydantic import AnyUrl

from app.secbot.config import SecbotConfigComponent
from app.secbot.handlers import SecbotOutputHandler
from app.secbot.inputs.gitlab.handlers.defectdojo.services import (
    OutputResultObject,
    send_result,
)
from app.secbot.inputs.gitlab.handlers.defectdojo.validator import (
    DefectDojoFindingsValidator,
)
from app.secbot.inputs.gitlab.schemas import GitlabOutputResult, GitlabScanResult
from app.secbot.inputs.gitlab.schemas.output_responses import OutputResponse
from app.secbot.inputs.gitlab.services import complete_scan, handle_exception
from app.secbot.inputs.gitlab.utils import get_project_name
from app.secbot.schemas import SecbotBaseModel


class DefectDojoCredentials(SecbotBaseModel):
    url: AnyUrl
    secret_key: str
    user: str
    lead_id: int


# noinspection PyMethodOverriding
class DefectDojoHandler(SecbotOutputHandler):
    env_model = DefectDojoCredentials

    async def on_failure(
        self,
        scan_result: GitlabScanResult,
        exception,
        component_name: str,
        env: DefectDojoCredentials,
    ):
        await handle_exception(
            check_id=scan_result.input.db_check_id,
            scan_component_name=scan_result.component_name,
            exception=exception,
        )

    async def fetch_status(
        self,
        eligible_scans: List[SecbotConfigComponent],
        commit_hash: str,
        env: DefectDojoCredentials,
    ) -> bool:
        dd_validator = DefectDojoFindingsValidator(
            eligible_scans=eligible_scans,
            credentials=env,
            commit_hash=commit_hash,
        )
        return await dd_validator.is_valid()

    async def run(
        self,
        scan_result: GitlabScanResult,
        component_name: str,
        env: DefectDojoCredentials,
    ):
        test_id, dd_findings = await send_result(
            credentials=env,
            output_result=OutputResultObject(
                data=scan_result.input.data,
                worker=scan_result.handler_name,
                result=json.dumps(scan_result.file.content),
            ),
        )
        await complete_scan(
            scan_id=scan_result.db_id,
            output_component_name=component_name,
            output_external_test_id=test_id,
        )
        response = OutputResponse(
            project_name=get_project_name(scan_result.input.data.project.git_ssh_url),
            project_url=scan_result.input.data.project.web_url,
            findings=dd_findings,
        )
        return GitlabOutputResult(
            handler_name=self.config_name,
            component_name=component_name,
            scan_result=scan_result,
            response=response,
        )
