from unittest import mock

from app.secbot import SecurityBot
from app.secbot.handlers import SecbotScanHandler
from app.secbot.inputs import SecbotInput
from app.secbot.inputs.gitlab import GitlabInput


def test_register_new_input():
    celery_app = mock.Mock()
    init_mock = mock.Mock(return_value=None)

    class ExampleInput(SecbotInput):
        __init__ = init_mock

    runner = SecurityBot(celery_app=celery_app)
    runner.register_input("new_input", ExampleInput)

    assert "new_input" in runner._registered_inputs
    init_mock.assert_called_once_with(config_name="new_input", celery_app=celery_app)


def test_register_new_handler():
    celery_app = mock.Mock()
    init_mock = mock.Mock(return_value=None)

    class ExampleScanHandler(SecbotScanHandler):
        __init__ = init_mock

        async def run(self, *args, **kwargs):
            pass

    gitlab_input = GitlabInput(config_name="gitlab", celery_app=celery_app)
    gitlab_input.register_handler("new_handler", ExampleScanHandler)

    assert "new_handler" in gitlab_input.scans
    init_mock.assert_called_once_with(config_name="new_handler", celery_app=celery_app)
