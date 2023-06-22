import pytest
import yaml

from app.secbot.config import SecbotConfig
from app.secbot.exceptions import SecbotConfigError
from app.secbot.inputs.gitlab.schemas import GitlabEvent


def test_parse_yaml_with_repo_regex_exclude(get_event_data):
    yaml_string = """
        version: "1.0" 
        components:
            gitleaks:
                handler_name: gitleaks
            defectdojo:
                handler_name: defectdojo
            slack:
                handler_name: slack
        jobs:
          - name: Exclude gitlab
            rules:
              gitlab:
                  event_type: "merge_request"
                  project.path_with_namespace: "!secbot-test-group/.*"
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack

          - name: Another merge request
            rules:
              gitlab:
                  event_type: "merge_request"
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack
              
          - name: Some job merge request
            rules:
              gitlab:
                  event_type: "push_tags"
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack
    """  # noqa: W291,E261

    yaml_config = SecbotConfig(yaml.safe_load(yaml_string))
    data = get_event_data(
        GitlabEvent.MERGE_REQUEST,
        {"project": {"path_with_namespace": "secbot-test-group/example-project"}},
    )
    assert yaml_config.matching_workflow_job("gitlab", data=data)


def test_parse_yaml_with_repo_regex(get_event_data):
    yaml_string = """
        version: "1.0" 
        components:
            gitleaks:
                handler_name: gitleaks
            defectdojo:
                handler_name: defectdojo
            slack:
                handler_name: slack
        jobs:
          - name: Exclude gitlab
            rules:
              gitlab:
                  event_type: "merge_request"
                  project.path_with_namespace: "secbot-test-group/.*"
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack

          - name: Another merge request
            rules:
              gitlab:
                  event_type: "merge_request"
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack
              
          - name: Some other job
            rules:
              gitlab:
                  event_type: "push_tags"
              example:
            scans:
              - gitleaks
            outputs:
              - defectdojo
            notifications:
              - slack
    """  # noqa: W291,E261
    secbot_config = SecbotConfig(yaml.safe_load(yaml_string))
    data = get_event_data(
        GitlabEvent.MERGE_REQUEST,
        {"project": {"path_with_namespace": "secbot-test-group/example-project"}},
    )
    with pytest.raises(SecbotConfigError):
        secbot_config.matching_workflow_job("gitlab", data=data)
