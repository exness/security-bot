import timeit

from celery import signals

from app.metrics.common import get_location_labels_from_env
from app.metrics.job import SRE_JOB_ERRORS, SRE_JOB_EXECUTION_TIME, SRE_JOB_EXECUTIONS


def prerun(task, *args, **kwargs):
    task._started_at = timeit.default_timer()


def postrun(task, *args, **kwargs):
    labels = get_location_labels_from_env()
    labels["job_name"] = task.name
    execution_time = int((timeit.default_timer() - task._started_at) * 1000)
    SRE_JOB_EXECUTIONS.labels(**labels).inc()
    SRE_JOB_EXECUTION_TIME.labels(**labels).inc(execution_time)


def on_error(exception, sender, *args, **kwargs):
    labels = get_location_labels_from_env()
    SRE_JOB_ERRORS.labels(
        **labels, job_name=sender.name, job_error=type(exception).__qualname__
    ).inc()


def instrument():
    signals.task_prerun.connect(prerun, weak=False)
    signals.task_postrun.connect(postrun, weak=False)
    signals.task_failure.connect(on_error, weak=False)
    signals.task_internal_error.connect(on_error, weak=False)
