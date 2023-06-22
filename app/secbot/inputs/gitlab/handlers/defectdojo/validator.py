from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel

import app.secbot.inputs.gitlab.handlers.defectdojo.api as defectdojo
from app.secbot.config import SecbotConfigComponent
from app.secbot.inputs.gitlab.handlers.defectdojo.services import (
    DefectDojoCredentials,
    handle_dd_response,
)
from app.secbot.inputs.gitlab.schemas.base import CommitHash
from app.secbot.schemas import Severity

Findings = TypeVar("Findings", bound=List[Dict[Any, Any]])


class DefectDojoFindingDuplicate(BaseModel):
    active: bool
    severity: Severity


class DefectDojoFindings(BaseModel):
    scan_name: str
    active: bool
    severity: Severity
    duplicate: Optional[DefectDojoFindingDuplicate] = None

    @property
    def is_active(self) -> bool:
        """Check if the finding is active.

        This method returns whether the finding is considered active or not.
        If the finding has a duplicate attribute,
        the method returns the active attribute of the duplicate object.
        """
        if self.duplicate:
            return self.duplicate.active
        return self.active


def is_gitleaks_valid(findings: List[DefectDojoFindings]) -> bool:
    """Check if the findings from Gitleaks are valid.

    This function checks if the findings from the Gitleaks scan service are valid.

    If all findings are inactive the function returns True.
    """
    assert all(finding.scan_name == "gitleaks" for finding in findings)
    for finding in findings:
        if finding.is_active:
            return False
    return True


class DefectDojoFindingsValidator:
    """Validator for DefectDojo findings.

    Based on findings from specific commit hash and by provided validators
    """

    class Meta:
        validators = {
            "gitleaks": is_gitleaks_valid,
        }
        scan_type_name = {
            "Gitleaks Scan": "gitleaks",
        }

    def __init__(
        self,
        eligible_scans: List[SecbotConfigComponent],
        credentials: DefectDojoCredentials,
        commit_hash: CommitHash,
    ):
        self.eligible_scans = eligible_scans
        self.commit_hash = commit_hash
        self.credentials = credentials

    async def _fetch_findings(self):
        dd = defectdojo.DefectDojoAPIv2(
            self.credentials.url,
            self.credentials.secret_key,
            self.credentials.user,
            debug=False,
            timeout=360,
        )
        response = await dd.list_findings(
            # NOTE(iz): We send commit_hash as a test tag to all scans
            #           by this param we filter results and get all findings
            #           based on specific security check
            test_tags=[self.commit_hash],
            related_fields=True,
            prefetch=["duplicate_finding"],
            # NOTE(ivan.zhirov): Temporary solution before the pagination system
            #                    will be added
            # TODO(ivan.zhirov): Implement proper pagination
            limit=500,
        )
        response = handle_dd_response(response)
        duplicates = response["prefetch"].get("duplicate_finding", {})
        for finding in response["results"]:
            duplicate_finding = None
            if duplicate_finding_id := finding.get("duplicate_finding"):
                duplicate_dict = duplicates[str(duplicate_finding_id)]
                duplicate_finding = DefectDojoFindingDuplicate(
                    active=duplicate_dict["active"],
                    severity=Severity(duplicate_dict["severity"]),
                )
            yield DefectDojoFindings(
                severity=finding["severity"],
                duplicate=duplicate_finding,
                active=finding["active"],
                scan_name=self.Meta.scan_type_name[
                    finding["related_fields"]["test"]["test_type"]["name"]
                ],
            )

    async def is_valid(self) -> bool:
        """Check if the current instance of the class is valid.

        This function checks if all the findings from the scan services are valid
        by using the validators specified in the validators attribute.
        """
        all_findings = [finding async for finding in self._fetch_findings()]
        eligible_scan_handler_names = [
            scan.handler_name for scan in self.eligible_scans
        ]
        validators = {
            check_service: validator
            for check_service, validator in self.Meta.validators.items()
            if check_service in eligible_scan_handler_names
        }
        for check_service, validator in validators.items():
            findings = [
                finding
                for finding in all_findings
                if finding.scan_name == check_service
            ]
            if not validator(findings):
                return False
        return True
