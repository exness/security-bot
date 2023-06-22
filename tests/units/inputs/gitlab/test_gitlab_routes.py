import pytest
from starlette.testclient import TestClient

from app.main import app
from app.secbot.inputs.gitlab.dependencies import get_gitlab_webhook_token_header

client = TestClient(app)
app.dependency_overrides[get_gitlab_webhook_token_header] = lambda: "token"


@pytest.mark.asyncio
async def test_gitlab_route_not_failed_with_invalid_data_event(faker):
    invalid_merge_request_data = {
        "event_type": "merge_request",
        **faker.pydict(allowed_types=["str", "int", "float", "bool"]),
    }
    response = client.post(
        "/v1/gitlab/webhook",
        headers={"X-Gitlab-Event": "Merge Request Hook"},
        json=invalid_merge_request_data,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
