from app.secbot.inputs.gitlab.schemas import GitlabEvent, MergeRequestWebhookModel


def test_merge_request_webhook_data_commit(get_event_data, faker):
    commit_hash = faker.md5()
    data = get_event_data(
        GitlabEvent.MERGE_REQUEST,
        {"object_attributes": {"last_commit": {"id": commit_hash}}},
    )
    instance = MergeRequestWebhookModel(**data)
    assert instance.commit.id == commit_hash


def test_merge_request_webhook_data_target_branch(get_event_data, faker):
    target_branch = faker.pystr()
    data = get_event_data(
        GitlabEvent.MERGE_REQUEST,
        {"object_attributes": {"target_branch": target_branch}},
    )
    instance = MergeRequestWebhookModel(**data)
    assert instance.target_branch == target_branch


def test_merge_request_webhook_data_path(get_event_data, faker):
    path = faker.uri()
    data = get_event_data(
        GitlabEvent.MERGE_REQUEST, {"object_attributes": {"url": path}}
    )
    instance = MergeRequestWebhookModel(**data)
    assert instance.path == path
