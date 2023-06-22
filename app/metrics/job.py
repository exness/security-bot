from prometheus_client import Counter

from app.metrics.common import location_labels

SRE_JOB_EXECUTIONS = Counter(
    "job_executions_total",
    "Total amount of executions",
    ("job_name", *location_labels),
)

SRE_JOB_EXECUTION_TIME = Counter(
    "job_execution_time_total",
    "Execution time",
    ("job_name", *location_labels),
)

SRE_JOB_ERRORS = Counter(
    "job_errors_total",
    "Amount of errors",
    ("job_name", "job_error", *location_labels),
)
