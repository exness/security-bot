import typing

from prometheus_client import Counter

from app.metrics.common import (
    LocationLabels,
    get_location_labels_from_env,
    location_labels,
)


class ConstCommonLabels(LocationLabels):
    db: str
    db_host: str
    db_port: str


common_labels = (*ConstCommonLabels.__annotations__, "db_query")


SRE_DB_CONNECTIONS = Counter(
    "db_client_connections_total",
    "Total amount of connections",
    ("db", "db_host", "db_port", *location_labels),
)

SRE_DB_QUERY_TOTAL = Counter("db_client_query_total", "Query counter", common_labels)

SRE_DB_QUERY_TIME = Counter(
    "db_client_query_time_total",
    "Query execution time",
    common_labels,
)

SRE_DB_RESPONSE_SIZE = Counter(
    "db_client_query_bytes_total",
    "Bytes in the response",
    common_labels,
)

SRE_DB_RESPONSE_RECORDS = Counter(
    "db_client_query_records_total",
    "Amount of records in the response",
    common_labels,
)

SRE_DB_QUERY_ERRORS = Counter(
    "db_client_query_errors_total",
    "Total number of errors on each query",
    common_labels,
)


def get_const_common_labels(
    db: str, db_host: str, db_port: typing.Union[str, int]
) -> ConstCommonLabels:
    loc_labels = get_location_labels_from_env()
    return {
        "dc": loc_labels["dc"],
        "cluster": loc_labels["cluster"],
        "host": loc_labels["host"],
        "k8s_namespace": loc_labels["k8s_namespace"],
        "k8s_kind": loc_labels["k8s_kind"],
        "k8s_pod": loc_labels["k8s_pod"],
        "k8s_container": loc_labels["k8s_container"],
        "docker_container": loc_labels["docker_container"],
        "os_process": loc_labels["os_process"],
        "os_process_cmdline": loc_labels["os_process_cmdline"],
        "team": loc_labels["team"],
        "service": loc_labels["service"],
        "db": db,
        "db_host": db_host,
        "db_port": str(db_port),
    }
