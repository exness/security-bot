from app.secbot.inputs.gitlab.schemas import GitlabEvent, PushWebhookModel


def test_push_webhook_data_commit(get_event_data, generate_commit_data, faker):
    commit_hash = faker.md5()
    data = get_event_data(
        GitlabEvent.PUSH,
        {
            "after": commit_hash,
            "commits": [
                generate_commit_data(),
                generate_commit_data(
                    {
                        "id": commit_hash,
                    }
                ),
            ],
        },
    )
    instance = PushWebhookModel(**data)
    assert instance.commit.id == commit_hash


def test_push_webhook_data_target_branch(get_event_data, faker):
    target_branch = faker.pystr()
    data = get_event_data(
        GitlabEvent.PUSH,
        {"ref": f"ref/heads/{target_branch}"},
    )
    instance = PushWebhookModel(**data)
    assert instance.target_branch == target_branch


def test_push_webhook_data_path(get_event_data, generate_commit_data, faker):
    commit_hash = faker.md5()
    path = faker.uri()
    data = get_event_data(
        GitlabEvent.PUSH,
        {
            "after": commit_hash,
            "commits": [
                generate_commit_data(),
                generate_commit_data(
                    {
                        "id": commit_hash,
                        "url": path,
                    }
                ),
            ],
        },
    )
    instance = PushWebhookModel(**data)
    assert instance.path == path
