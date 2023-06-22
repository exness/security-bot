import pytest

from app.secbot.inputs.gitlab.handlers.defectdojo.validator import (
    DefectDojoFindingDuplicate,
    DefectDojoFindings,
    is_gitleaks_valid,
)
from app.secbot.schemas import Severity


def test_which_finding_active_without_duplicate(faker):
    is_valid = faker.pybool()
    finding = DefectDojoFindings(
        active=is_valid,
        scan_name="gitleaks",
        severity=Severity.HIGH,
        duplicate=None,
    )
    assert finding.is_active is is_valid


def test_which_finding_active_with_duplicate():
    duplicate = DefectDojoFindingDuplicate(
        active=True,
        severity=Severity.HIGH,
    )
    finding = DefectDojoFindings(
        active=False,
        scan_name="gitleaks",
        severity=Severity.HIGH,
        duplicate=duplicate,
    )
    assert finding.is_active is True


def test_is_gitleaks_with_wrong_check_service_type():
    findings = [
        DefectDojoFindings(
            active=True,
            scan_name="some-other-service",
            severity=Severity.HIGH,
            duplicate=None,
        ),
        DefectDojoFindings(
            active=True,
            scan_name="gitleaks",
            severity=Severity.HIGH,
            duplicate=None,
        ),
    ]
    with pytest.raises(AssertionError):
        is_gitleaks_valid(findings)


@pytest.mark.parametrize(
    "findings, expected",
    [
        ([], True),
        # No matter severities. If there is an active finding, the function returns False
        (
            [
                DefectDojoFindings(
                    active=True,
                    scan_name="gitleaks",
                    severity=Severity.INFO,
                    duplicate=None,
                ),
                DefectDojoFindings(
                    active=True,
                    scan_name="gitleaks",
                    severity=Severity.LOW,
                    duplicate=None,
                ),
            ],
            False,
        ),
        # All findings are inactive
        (
            [
                DefectDojoFindings(
                    active=False,
                    scan_name="gitleaks",
                    severity=Severity.CRITICAL,
                    duplicate=None,
                ),
                DefectDojoFindings(
                    active=False,
                    scan_name="gitleaks",
                    severity=Severity.HIGH,
                    duplicate=None,
                ),
            ],
            True,
        ),
        # Active in duplicate
        (
            [
                DefectDojoFindings(
                    active=False,
                    scan_name="gitleaks",
                    severity=Severity.CRITICAL,
                    duplicate=DefectDojoFindingDuplicate(
                        active=True,
                        severity=Severity.CRITICAL,
                    ),
                ),
                DefectDojoFindings(
                    active=False,
                    scan_name="gitleaks",
                    severity=Severity.HIGH,
                    duplicate=None,
                ),
            ],
            False,
        ),
    ],
)
def test_is_gitleaks_valid(findings, expected):
    assert is_gitleaks_valid(findings) == expected
