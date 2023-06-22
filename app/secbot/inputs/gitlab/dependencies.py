from __future__ import annotations

import logging
from typing import Optional

from fastapi import Body, Depends, Header, HTTPException, Request
from pydantic import ValidationError

from app.secbot.inputs.gitlab.schemas import (
    AnyGitlabModel,
    GitlabEvent,
    get_gitlab_model_for_event,
)
from app.settings import settings

logger = logging.getLogger(__name__)


def get_gitlab_webhook_token_header(x_gitlab_token: str = Header(None)) -> str:
    tokens = [
        config.webhook_secret_token.get_secret_value()
        for config in settings.gitlab_configs
    ]
    # TODO: add auth for projects based on token
    if x_gitlab_token not in tokens:
        raise HTTPException(status_code=403, detail="X-Gitlab-Token header is invalid")
    return x_gitlab_token


async def gitlab_event(
    request: Request,
    x_gitlab_event: Optional[str] = Header(None),
) -> Optional[GitlabEvent]:
    """Get GitlabEvent model from http request.

    We may have any types of events, not only which we support.
    If we don't support event, we just return 200 to the gitlab and do nothing.
    """

    # System Hook happens when event triggered by gitlab itself
    if x_gitlab_event == "System Hook":
        event_map = {
            "merge_request": GitlabEvent.MERGE_REQUEST,
            "push": GitlabEvent.PUSH,
            "tag_push": GitlabEvent.TAG_PUSH,
        }
        body = await request.json()
        # NOTE(ivan.zhirov): For some reason gitlab has different event key names
        #                    for different events.
        #                    PUSH - event_name
        #                    TAG_PUSH - event_name
        #                    MERGE_REQUEST - event_type
        event_name = body.get("event_name", body.get("event_type"))
        try:
            return event_map[event_name]
        except KeyError:
            return None

    # Web Hook happens when event triggered by particular project
    try:
        return GitlabEvent(x_gitlab_event)
    except ValueError:
        return None


def webhook_model(
    body: dict = Body(
        examples={
            GitlabEvent.MERGE_REQUEST: {
                "value": {
                    "object_kind": "merge_request",
                    "event_type": "merge_request",
                    "user": {
                        "id": 1,
                        "name": "Administrator",
                        "username": "root",
                        "avatar_url": "https://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon",
                        "email": "admin@example.com",
                    },
                    "project": {
                        "id": 1,
                        "name": "Gitlab Test",
                        "description": "Aut reprehenderit ut est.",
                        "web_url": "https://example.com/gitlabhq/gitlab-test",
                        "avatar_url": None,
                        "git_ssh_url": "git@example.com:gitlabhq/gitlab-test.git",
                        "git_http_url": "https://example.com/gitlabhq/gitlab-test.git",
                        "namespace": "GitlabHQ",
                        "visibility_level": 20,
                        "path_with_namespace": "gitlabhq/gitlab-test",
                        "default_branch": "master",
                        "homepage": "https://example.com/gitlabhq/gitlab-test",
                        "url": "https://example.com/gitlabhq/gitlab-test.git",
                        "ssh_url": "git@example.com:gitlabhq/gitlab-test.git",
                        "http_url": "https://example.com/gitlabhq/gitlab-test.git",
                    },
                    "repository": {
                        "name": "Gitlab Test",
                        "url": "https://example.com/gitlabhq/gitlab-test.git",
                        "description": "Aut reprehenderit ut est.",
                        "homepage": "https://example.com/gitlabhq/gitlab-test",
                    },
                    "object_attributes": {
                        "id": 99,
                        "iid": 1,
                        "target_branch": "master",
                        "source_branch": "ms-viewport",
                        "source_project_id": 14,
                        "author_id": 51,
                        "assignee_ids": [6],
                        "assignee_id": 6,
                        "reviewer_ids": [6],
                        "title": "MS-Viewport",
                        "created_at": "2013-12-03T17:23:34Z",
                        "updated_at": "2013-12-03T17:23:34Z",
                        "milestone_id": None,
                        "state": "opened",
                        "blocking_discussions_resolved": True,
                        "work_in_progress": False,
                        "first_contribution": True,
                        "merge_status": "unchecked",
                        "target_project_id": 14,
                        "description": "",
                        "url": "https://example.com/diaspora/merge_requests/1",
                        "source": {
                            "name": "Awesome Project",
                            "description": "Aut reprehenderit ut est.",
                            "web_url": "https://example.com/awesome_space/awesome_project",
                            "avatar_url": None,
                            "git_ssh_url": "git@example.com:awesome_space/awesome_project.git",
                            "git_http_url": "https://example.com/awesome_space/awesome_project.git",
                            "namespace": "Awesome Space",
                            "visibility_level": 20,
                            "path_with_namespace": "awesome_space/awesome_project",
                            "default_branch": "master",
                            "homepage": "https://example.com/awesome_space/awesome_project",
                            "url": "https://example.com/awesome_space/awesome_project.git",
                            "ssh_url": "git@example.com:awesome_space/awesome_project.git",
                            "http_url": "https://example.com/awesome_space/awesome_project.git",
                        },
                        "target": {
                            "name": "Awesome Project",
                            "description": "Aut reprehenderit ut est.",
                            "web_url": "https://example.com/awesome_space/awesome_project",
                            "avatar_url": None,
                            "git_ssh_url": "git@example.com:awesome_space/awesome_project.git",
                            "git_http_url": "https://example.com/awesome_space/awesome_project.git",
                            "namespace": "Awesome Space",
                            "visibility_level": 20,
                            "path_with_namespace": "awesome_space/awesome_project",
                            "default_branch": "master",
                            "homepage": "https://example.com/awesome_space/awesome_project",
                            "url": "https://example.com/awesome_space/awesome_project.git",
                            "ssh_url": "git@example.com:awesome_space/awesome_project.git",
                            "http_url": "https://example.com/awesome_space/awesome_project.git",
                        },
                        "last_commit": {
                            "id": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                            "message": "fixed readme",
                            "timestamp": "2012-01-03T23:36:29+02:00",
                            "url": "https://example.com/awesome_space/awesome_project/commits/da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                            "author": {
                                "name": "GitLab dev user",
                                "email": "gitlabdev@dv6700.(none)",
                            },
                        },
                        "labels": [
                            {
                                "id": 206,
                                "title": "API",
                                "color": "#ffffff",
                                "project_id": 14,
                                "created_at": "2013-12-03T17:15:43Z",
                                "updated_at": "2013-12-03T17:15:43Z",
                                "template": False,
                                "description": "API related issues",
                                "type": "ProjectLabel",
                                "group_id": 41,
                            }
                        ],
                        "action": "open",
                        "detailed_merge_status": "mergeable",
                    },
                    "labels": [
                        {
                            "id": 206,
                            "title": "API",
                            "color": "#ffffff",
                            "project_id": 14,
                            "created_at": "2013-12-03T17:15:43Z",
                            "updated_at": "2013-12-03T17:15:43Z",
                            "template": False,
                            "description": "API related issues",
                            "type": "ProjectLabel",
                            "group_id": 41,
                        }
                    ],
                    "changes": {
                        "updated_by_id": {"previous": None, "current": 1},
                        "updated_at": {
                            "previous": "2017-09-15 16:50:55 UTC",
                            "current": "2017-09-15 16:52:00 UTC",
                        },
                        "labels": {
                            "previous": [
                                {
                                    "id": 206,
                                    "title": "API",
                                    "color": "#ffffff",
                                    "project_id": 14,
                                    "created_at": "2013-12-03T17:15:43Z",
                                    "updated_at": "2013-12-03T17:15:43Z",
                                    "template": False,
                                    "description": "API related issues",
                                    "type": "ProjectLabel",
                                    "group_id": 41,
                                }
                            ],
                            "current": [
                                {
                                    "id": 205,
                                    "title": "Platform",
                                    "color": "#123123",
                                    "project_id": 14,
                                    "created_at": "2013-12-03T17:15:43Z",
                                    "updated_at": "2013-12-03T17:15:43Z",
                                    "template": False,
                                    "description": "Platform related issues",
                                    "type": "ProjectLabel",
                                    "group_id": 41,
                                }
                            ],
                        },
                    },
                    "assignees": [
                        {
                            "id": 6,
                            "name": "User1",
                            "username": "user1",
                            "avatar_url": "https://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon",
                        }
                    ],
                    "reviewers": [
                        {
                            "id": 6,
                            "name": "User1",
                            "username": "user1",
                            "avatar_url": "https://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=40\u0026d=identicon",
                        }
                    ],
                }
            },
            GitlabEvent.TAG_PUSH: {
                "value": {
                    "object_kind": "tag_push",
                    "event_name": "tag_push",
                    "before": "0000000000000000000000000000000000000000",
                    "after": "82b3d5ae55f7080f1e6022629cdb57bfae7cccc7",
                    "ref": "refs/tags/v1.0.0",
                    "checkout_sha": "82b3d5ae55f7080f1e6022629cdb57bfae7cccc7",
                    "user_id": 1,
                    "user_name": "John Smith",
                    "user_avatar": "https://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=8://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=80",
                    "project_id": 1,
                    "project": {
                        "id": 1,
                        "name": "Example",
                        "description": "",
                        "web_url": "https://example.com/jsmith/example",
                        "avatar_url": None,
                        "git_ssh_url": "git@example.com:jsmith/example.git",
                        "git_http_url": "https://example.com/jsmith/example.git",
                        "namespace": "Jsmith",
                        "visibility_level": 0,
                        "path_with_namespace": "jsmith/example",
                        "default_branch": "master",
                        "homepage": "https://example.com/jsmith/example",
                        "url": "git@example.com:jsmith/example.git",
                        "ssh_url": "git@example.com:jsmith/example.git",
                        "http_url": "https://example.com/jsmith/example.git",
                    },
                    "repository": {
                        "name": "Example",
                        "url": "ssh://git@example.com/jsmith/example.git",
                        "description": "",
                        "homepage": "https://example.com/jsmith/example",
                        "git_http_url": "https://example.com/jsmith/example.git",
                        "git_ssh_url": "git@example.com:jsmith/example.git",
                        "visibility_level": 0,
                    },
                    "commits": [],
                    "total_commits_count": 0,
                }
            },
            GitlabEvent.PUSH: {
                "value": {
                    "object_kind": "push",
                    "event_name": "push",
                    "before": "95790bf891e76fee5e1747ab589903a6a1f80f22",
                    "after": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                    "ref": "refs/heads/master",
                    "checkout_sha": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                    "user_id": 4,
                    "user_name": "John Smith",
                    "user_username": "jsmith",
                    "user_email": "john@example.com",
                    "user_avatar": "https://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=8://s.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?s=80",
                    "project_id": 15,
                    "project": {
                        "id": 15,
                        "name": "Diaspora",
                        "description": "",
                        "web_url": "https://example.com/mike/diaspora",
                        "avatar_url": None,
                        "git_ssh_url": "git@example.com:mike/diaspora.git",
                        "git_http_url": "https://example.com/mike/diaspora.git",
                        "namespace": "Mike",
                        "visibility_level": 0,
                        "path_with_namespace": "mike/diaspora",
                        "default_branch": "master",
                        "homepage": "https://example.com/mike/diaspora",
                        "url": "git@example.com:mike/diaspora.git",
                        "ssh_url": "git@example.com:mike/diaspora.git",
                        "http_url": "https://example.com/mike/diaspora.git",
                    },
                    "repository": {
                        "name": "Diaspora",
                        "url": "git@example.com:mike/diaspora.git",
                        "description": "",
                        "homepage": "https://example.com/mike/diaspora",
                        "git_http_url": "https://example.com/mike/diaspora.git",
                        "git_ssh_url": "git@example.com:mike/diaspora.git",
                        "visibility_level": 0,
                    },
                    "commits": [
                        {
                            "id": "b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
                            "message": "Update Catalan translation to e38cb41.\n\nSee https://gitlab.com/gitlab-org/gitlab for more information",
                            "title": "Update Catalan translation to e38cb41.",
                            "timestamp": "2011-12-12T14:27:31+02:00",
                            "url": "https://example.com/mike/diaspora/commit/b6568db1bc1dcd7f8b4d5a946b0b91f9dacd7327",
                            "author": {
                                "name": "Jordi Mallach",
                                "email": "jordi@softcatala.org",
                            },
                            "added": ["CHANGELOG"],
                            "modified": ["app/controller/application.rb"],
                            "removed": [],
                        },
                        {
                            "id": "da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                            "message": "fixed readme",
                            "title": "fixed readme",
                            "timestamp": "2012-01-03T23:36:29+02:00",
                            "url": "https://example.com/mike/diaspora/commit/da1560886d4f094c3e6c9ef40349f7d38b5d27d7",
                            "author": {
                                "name": "GitLab dev user",
                                "email": "gitlabdev@dv6700.(none)",
                            },
                            "added": ["CHANGELOG"],
                            "modified": ["app/controller/application.rb"],
                            "removed": [],
                        },
                    ],
                    "total_commits_count": 4,
                }
            },
        }
    ),
    event: Optional[GitlabEvent] = Depends(gitlab_event),
) -> Optional[AnyGitlabModel]:
    """Get GitlabEvent model base."""
    try:
        return get_gitlab_model_for_event(event, body)
    except (KeyError, ValidationError):
        return None
