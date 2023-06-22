from typing import Optional

import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from app.secbot.inputs.gitlab.handlers.slack import generate_message_blocks
from app.secbot.inputs.gitlab.schemas import (
    GitlabOutputResult,
    GitlabScanResult,
    GitlabScanResultFile,
)
from app.secbot.inputs.gitlab.schemas.output_responses import (
    OutputFinding,
    OutputResponse,
)


class GitlabScanResultFileFactory(ModelFactory[GitlabScanResultFile]):
    __model__ = GitlabScanResultFile

    content = {}


class GitlabScanResultFactory(ModelFactory[GitlabScanResult]):
    __model__ = GitlabScanResult

    file = GitlabScanResultFileFactory.build()


class OutputResultFactory(ModelFactory[GitlabOutputResult]):
    __model__ = GitlabOutputResult

    scan_result = GitlabScanResultFactory.build()


class FindingFactory(ModelFactory[OutputFinding]):
    __model__ = OutputFinding


@pytest.fixture
def output_result_factory(faker):
    def factory(
        findings_size: int = 10,
        project_name: Optional[str] = None,
        project_url: Optional[str] = None,
    ):
        if not project_name:
            project_name = faker.pystr()

        if not project_url:
            project_url = faker.uri()

        return OutputResultFactory.build(
            response=OutputResponse(
                project_name=project_name,
                project_url=project_url,
                findings=FindingFactory.batch(size=findings_size),
            ),
        )

    return factory


def generate_slack_message_block(msg: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": msg}}


def test_slack_message_generation_with_correct_worker_name(
    output_result_factory, faker
):
    findings_size = faker.pyint(max_value=25)
    project_name = faker.pystr()
    project_url = faker.uri()

    output_result = output_result_factory(
        project_name=project_name,
        project_url=project_url,
        findings_size=findings_size,
    )
    message_blocks = generate_message_blocks(output_result, render_limit=10)
    assert message_blocks is not None

    worker_name = output_result.scan_result.component_name

    # Check that the title has correct worker name and project name
    assert message_blocks[0] == generate_slack_message_block(
        f"Worker *{worker_name}* found *{findings_size}* new findings in *<{project_url}|{project_name}>*:"
    )


def test_slack_message_generation_without_findings(output_result_factory):
    output_result = output_result_factory(findings_size=0)
    assert generate_message_blocks(output_result, render_limit=10) is None


def test_slack_message_generation_with_extra_limit(output_result_factory):
    render_limit = 10
    findings_size = 15
    output_result = output_result_factory(findings_size=findings_size)

    message_blocks = generate_message_blocks(output_result, render_limit=render_limit)
    assert message_blocks is not None

    # Plus header and footer
    assert len(message_blocks) == render_limit + 2

    # Assert footer
    assert message_blocks[-1] == generate_slack_message_block(
        f":no_bell: *{findings_size - render_limit}* were *stripped* from notification :no_bell:"
    )
