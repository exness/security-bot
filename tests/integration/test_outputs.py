from unittest import mock

import pytest

from app.secbot.inputs.gitlab.handlers.defectdojo.services import (
    OutputResultObject,
    send_result,
)
from tests.units.factories import create_merge_request_webhook__security_bot


@pytest.mark.asyncio
@pytest.mark.parametrize("fixture_file_path", ["gitleaks.json"])
@mock.patch("app.secbot.inputs.gitlab.handlers.defectdojo.services.dd_upload")
@mock.patch("app.secbot.inputs.gitlab.handlers.defectdojo.services.dd_get_test")
@mock.patch("app.secbot.inputs.gitlab.handlers.defectdojo.services.dd_prepare")
@mock.patch(
    "app.secbot.inputs.gitlab.handlers.defectdojo.services.dd_findings_by_test"
)
@mock.patch("app.secbot.inputs.gitlab.handlers.defectdojo.services.asyncio.sleep")
async def test_defectdojo_output(
    # TODO(ivan.zhirov): mock tests with time.sleep
    sleep,
    dd_findings_by_test,
    dd_prepare,
    dd_get_test,
    dd_upload,
    dir_tests,
    fixture_file_path,
):
    data = create_merge_request_webhook__security_bot()
    with open(
        dir_tests / "fixtures/worker_outputs" / fixture_file_path
    ) as output_data:
        result = OutputResultObject(
            data=data,
            worker=fixture_file_path.split(".")[0],
            result=output_data.read(),
        )

    dd_get_test.return_value = {"percent_complete": 100}

    # TODO(ivan.zhirov): mock the response from the server
    dd_findings_by_test.return_value = {"count": 1, "results": []}

    credentials = mock.Mock()

    assert await send_result(credentials=credentials, output_result=result)

    dd_prepare.assert_called_once()
    dd_upload.assert_called_once()
    dd_get_test.assert_called()
    dd_findings_by_test.assert_called_once()
