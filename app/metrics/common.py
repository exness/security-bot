import os
import typing
from sys import argv, executable

from prometheus_client import REGISTRY, CollectorRegistry, start_http_server
from prometheus_client.multiprocess import MultiProcessCollector

from app.metrics.constants import PROMETHEUS_MULTIPROC_DIR


class LocationLabels(typing.TypedDict):
    dc: str
    cluster: str
    host: str
    k8s_namespace: str
    k8s_kind: str
    k8s_pod: str
    k8s_container: str
    docker_container: str
    os_process: str
    os_process_cmdline: str
    team: str
    service: str


location_labels = tuple(LocationLabels.__annotations__)


def get_location_labels_from_env() -> LocationLabels:
    return {
        "dc": os.getenv("TRACING_TAGS_DC", ""),
        "cluster": os.getenv("TRACING_TAGS_CLUSTER", ""),
        "host": os.getenv("TRACING_TAGS_HOST", ""),
        "os_process": os.getenv("TRACING_TAGS_PROCESS_NAME", executable),
        "os_process_cmdline": " ".join(argv),
        "docker_container": os.getenv("TRACING_TAGS_DOCKER_CONTAINER", ""),
        "k8s_namespace": os.getenv("TRACING_TAGS_K8S_NAMESPACE", ""),
        "k8s_kind": os.getenv("TRACING_TAGS_K8S_KIND", ""),
        "k8s_pod": os.getenv("TRACING_TAGS_K8S_POD", ""),
        "k8s_container": os.getenv("TRACING_TAGS_K8S_CONTAINER", ""),
        "team": os.getenv("SRE_METRIC_LABEL_TEAM", ""),
        "service": os.getenv("SRE_METRIC_LABEL_SERVICE", ""),
    }


def start_http_metrics_server(port: int):
    if (
        PROMETHEUS_MULTIPROC_DIR in os.environ
        or PROMETHEUS_MULTIPROC_DIR.lower() in os.environ
    ):
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    start_http_server(port, registry=registry)
