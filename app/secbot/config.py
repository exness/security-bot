from __future__ import annotations

import os
import pathlib
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel

from app.secbot.exceptions import SecbotConfigError, SecbotConfigMissingEnv

ConfigInputName = str


# Represents a configuration component in the Secbot workflow.
class SecbotConfigComponent(BaseModel):
    name: str
    handler_name: str
    config: Optional[Dict[str, Any]] = None
    env: Optional[Dict[str, Any]] = None


# Represents a job in the Secbot workflow.
class WorkflowJob(BaseModel):
    name: str
    input_name: ConfigInputName
    rules: Optional[Dict[str, str]] = None
    scans: List[SecbotConfigComponent]
    outputs: List[SecbotConfigComponent]
    notifications: Optional[List[SecbotConfigComponent]] = None


def get_jsonpath_value(event_raw: dict, path: str):
    """Fetches a value from a dictionary by JSONPath.

    Args:
        event_raw (dict): Dictionary to fetch value from.
        path (str): JSONPath specifying value location.
    Returns:
        The value specified by the JSONPath.
    """
    try:
        key, rest_keys = path.split(".", 1)
        value = event_raw[key]
        if isinstance(value, dict):
            return get_jsonpath_value(value, rest_keys)
    except ValueError:
        key = path
    return event_raw[key]


def is_job_valid_for_rules(job: WorkflowJob, data: dict) -> bool:
    """Checks if the given job configuration matches the data.

    Args:
        job (WorkflowJob): Job to check.
        data (dict): Data to match against.
    Returns:
        bool: True if job's rules match the data.
    """
    if not (rules := job.rules or {}):
        return True

    for jsonpath, rule_regex in rules.items():
        value = get_jsonpath_value(data, jsonpath)
        if re.fullmatch(rule_regex, value) is None:
            return False
    return True


def config_parser(obj: dict) -> Dict[ConfigInputName, List[WorkflowJob]]:
    """Parses the configuration file (version 1.0).

    Args:
        obj (dict): Dictionary representing the configuration file.
    Returns:
        dict: Maps from input names to lists of jobs.
    """
    components = {}
    for component_name, component_data in obj["components"].items():
        parsed_env = {}
        for key, value in component_data.get("env", {}).items():
            try:
                parsed_env[key] = os.getenv(value)
            except AttributeError:
                raise SecbotConfigMissingEnv(
                    f"Failed to parse env variable {value} "
                    f"for component {component_name}"
                )
        components[component_name] = SecbotConfigComponent(
            handler_name=component_data["handler_name"],
            name=component_name,
            config=component_data.get("config"),
            env=parsed_env or None,
        )

    if not components:
        raise SecbotConfigError("No components found in config")

    jobs = defaultdict(list)
    for job in obj["jobs"]:
        rules = job["rules"]

        # Combine names of components with component models
        job_scans = [components[name] for name in job["scans"]]
        job_outputs = [components[name] for name in job["outputs"]]
        job_notifications = [components[name] for name in job["notifications"]]

        for input_name in set(rules.keys()):
            jobs[input_name].append(
                WorkflowJob(
                    name=job["name"],
                    input_name=input_name,
                    rules=rules[input_name],
                    scans=job_scans,
                    outputs=job_outputs,
                    notifications=job_notifications,
                )
            )
    if not jobs:
        raise SecbotConfigError("No jobs found in config")
    return jobs


class SecbotConfig:
    """Represents the Secbot configuration file.

    Methods:
    - from_yml_file: Load configuration from a YAML file.
    - matching_workflow_job: Returns matching jobs.
    """

    # A dictionary that maps configuration version numbers to their corresponding
    # parser functions. The CONFIG_VERSION_PARSER is only responsible for
    # validating the configuration file itself. The security bot (secbot) will
    # handle the validation of the handlers separately.
    #
    # TODO(ivan.zhirov): Update the implementation to support versioning semantics,
    #                    including tilde and caret ranges.
    VERSIONS_PARSER = {
        "1.0": config_parser,
    }

    @classmethod
    def from_yml_file(cls, config_path: str) -> SecbotConfig:
        """Load Secbot configuration from a YAML file.

        Args:
            config_path (str): Path to the YAML file.
        Returns:
            SecbotConfig: Loaded Secbot configuration.
        """
        base_path = pathlib.Path(os.path.dirname(__file__))
        with open(base_path / config_path) as f:
            config_obj = yaml.safe_load(f.read())
        return cls(config_obj)

    def __init__(self, config_obj: dict):
        try:
            version = config_obj["version"]
        except KeyError:
            raise SecbotConfigError("Config version is not specified")
        try:
            parser = self.VERSIONS_PARSER[str(version)]
        except KeyError:
            raise SecbotConfigError(f"Unsupported config version: {version}")

        self.jobs: Dict[ConfigInputName, List[WorkflowJob]] = parser(config_obj)

    def matching_workflow_job(
        self,
        input_name: ConfigInputName,
        data: Dict[str, Any],
    ) -> Optional[WorkflowJob]:
        """Returns the job that matches a given input name and data.
        Currently, only one job per data is supported.

        Args:
            input_name (ConfigInputName): Input name to match.
            data (Dict[str, Any]): Data to match against.
        Returns:
            Optional[WorkflowJob]: Matching job, if exists; None otherwise.
        """
        ret = [
            job for job in self.jobs[input_name] if is_job_valid_for_rules(job, data)
        ]
        # TODO(ivan.zhirov): Currently, we only support one job per data.
        #                    Consider changing this in the future.
        if len(ret) > 1:
            raise SecbotConfigError(
                f"Multiple jobs found for input {input_name} and data {data}"
            )
        return next(iter(ret), None)


config = SecbotConfig.from_yml_file("../config.yml")
