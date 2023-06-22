from app.secbot.inputs.gitlab.schemas import GitlabEvent, TagWebhookModel


def test_tag_push_webhook_data_commit(get_event_data, generate_commit_data, faker):
    commit_hash = faker.md5()
    data = get_event_data(
        GitlabEvent.TAG_PUSH,
        {
            "checkout_sha": commit_hash,
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
    instance = TagWebhookModel(**data)
    assert instance.commit.id == commit_hash


def test_tag_push_webhook_data_target_branch(get_event_data, faker):
    target_branch = faker.pystr()
    data = get_event_data(
        GitlabEvent.TAG_PUSH,
        {"ref": f"ref/tags/{target_branch}"},
    )
    instance = TagWebhookModel(**data)
    assert instance.target_branch == target_branch


def test_tag_push_webhook_data_path(get_event_data, generate_commit_data, faker):
    commit_hash = faker.md5()
    path = faker.uri()
    data = get_event_data(
        GitlabEvent.TAG_PUSH,
        {
            "checkout_sha": commit_hash,
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
    instance = TagWebhookModel(**data)
    assert instance.path == path
