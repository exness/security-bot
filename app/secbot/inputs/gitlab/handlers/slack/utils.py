from typing import Dict, List, Optional

from app.secbot.inputs.gitlab.schemas import GitlabOutputResult
from app.secbot.schemas import Severity

SEVERITY_TO_EMOJI: Dict[Severity, str] = {
    Severity.INFO: ":white_circle:",
    Severity.LOW: ":large_green_circle:",
    Severity.MEDIUM: ":large_yellow_circle:",
    Severity.HIGH: ":large_orange_circle:",
    Severity.CRITICAL: ":red_circle:",
}


def generate_message_blocks(
    output: GitlabOutputResult,
    render_limit: int,
) -> Optional[List[Dict[str, str]]]:

    new_findings_count = len(output.response.findings)
    if new_findings_count == 0:
        return None

    message_blocks = []

    def add_to_message_blocks(msg: str) -> None:
        nonlocal message_blocks

        block = {"type": "section", "text": {"type": "mrkdwn", "text": msg}}
        message_blocks.append(block)

    # Message header
    project = output.response.project_name
    project_url = output.response.project_url
    message = f"Worker *{output.scan_result.component_name}* found *{new_findings_count}* new findings in *<{project_url}|{project}>*:"
    add_to_message_blocks(message)

    # Sort findings by severity and limit them
    findings = sorted(
        output.response.findings[:render_limit],
        key=lambda item: item.severity.priority,
    )

    # Add limited findings info text blocks
    for finding in findings:
        finding_severity = SEVERITY_TO_EMOJI.get(
            finding.severity, ":large_purple_circle:"
        )
        message = f"{finding_severity} <{finding.url}|{finding.title}>"
        add_to_message_blocks(message)

    # Add special info message block if findings count is greater than limit
    if new_findings_count > render_limit:
        message = f":no_bell: *{new_findings_count - render_limit}* were *stripped* from notification :no_bell:"
        add_to_message_blocks(message)

    return message_blocks
