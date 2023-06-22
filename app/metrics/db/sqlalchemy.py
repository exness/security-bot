import re
import timeit
import typing

from prometheus_client import Counter, Gauge
from sqlalchemy import event
from sqlalchemy.engine import Compiled, CursorResult, Engine, ExceptionContext
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.future import Connection
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import ClauseElement

from app.metrics.common import location_labels
from app.metrics.db.base import (
    SRE_DB_CONNECTIONS,
    SRE_DB_QUERY_ERRORS,
    SRE_DB_QUERY_TIME,
    SRE_DB_QUERY_TOTAL,
    ConstCommonLabels,
    get_const_common_labels,
)

EventClauseElement = typing.Union[ClauseElement, Compiled, str]
QueryLabelsGetter = typing.Callable[[EventClauseElement], typing.Dict[str, typing.Any]]
_DIGITS_REGEX = re.compile(r"\d+")


def add_event_listeners(
    engine: typing.Union[Engine, AsyncEngine],
    enable_pool_metrics: bool = False,
) -> None:
    """Add all currently implemented event listeners to the given engine."""

    const_labels = get_const_common_labels(
        db=engine.url.database,
        db_host=engine.url.host,
        db_port=engine.url.port,
    )
    sync_engine = engine if isinstance(engine, Engine) else engine.sync_engine

    event.listen(sync_engine, "connect", ConnectionsTotal(const_labels).on_connect)

    event.listen(
        sync_engine, "before_execute", QueryTotal(const_labels).on_before_execute
    )

    query_time = QueryTime(const_labels)
    event.listen(sync_engine, "before_execute", query_time.on_before_execute)
    event.listen(sync_engine, "after_execute", query_time.on_after_execute)
    event.listen(sync_engine, "handle_error", query_time.on_handle_error)

    event.listen(
        sync_engine, "handle_error", QueryErrorsTotal(const_labels).on_handle_error
    )

    if enable_pool_metrics and isinstance(sync_engine.pool, QueuePool):
        queue_pool_status = QueuePoolStatus(
            const_labels=const_labels, pool=sync_engine.pool
        )

        event.listen(sync_engine.pool, "checkin", queue_pool_status.checkin)
        event.listen(sync_engine.pool, "checkout", queue_pool_status.checkout)


class ConnectionsTotal:
    """Total count of connecting events."""

    def __init__(
        self, const_labels: ConstCommonLabels, metric: Counter = SRE_DB_CONNECTIONS
    ) -> None:
        self.const_labels = const_labels
        self.metric = metric

    def on_connect(
        self, dbapi_connection: typing.Any, connection_record: typing.Any
    ) -> None:
        self.metric.labels(**self.const_labels).inc()


class QueuePoolStatus:
    """
    Queue pool status.

    checked_in_metric: Total number of currently free connections in pool.
    checked_out_metric: Total count of currently checked out connections.
    overflow_metric: Total number of currently overflowed connections.
    """

    def __init__(
        self,
        const_labels: ConstCommonLabels,
        pool: QueuePool,
        checked_in_metric: typing.Optional[Gauge] = None,
        checked_out_metric: typing.Optional[Gauge] = None,
        overflow_metric: typing.Optional[Gauge] = None,
    ) -> None:
        self.pool = pool
        self.const_labels = const_labels

        self.checked_in_metric = checked_in_metric or Gauge(
            "db_client_free_connections_in_pool_total",
            "Total number of currently free connections in pool.",
            ("db", "db_host", "db_port", *location_labels),
        )
        self.checked_out_metric = checked_out_metric or Gauge(
            "db_client_connections_in_progress_total",
            "Total number of currently active connections.",
            ("db", "db_host", "db_port", *location_labels),
        )
        self.overflow_metric = overflow_metric or Gauge(
            "db_client_overflowed_connections_in_pool_total",
            "Total number of currently overflowed connections.",
            ("db", "db_host", "db_port", *location_labels),
        )

    def _status(self):
        self.checked_in_metric.labels(**self.const_labels).set(self.pool.checkedin())
        self.checked_out_metric.labels(**self.const_labels).set(self.pool.checkedout())
        self.overflow_metric.labels(**self.const_labels).set(self.pool.overflow())

    def checkout(
        self,
        dbapi_connection: typing.Any,
        connection_record: typing.Any,
        connection_proxy: typing.Any,
    ) -> None:
        self._status()

    def checkin(
        self, dbapi_connection: typing.Any, connection_record: typing.Any
    ) -> None:
        self._status()


def default_query_labels_getter(
    clauseelement: EventClauseElement,
) -> typing.Dict[str, typing.Any]:
    return {"db_query": get_query_name(clauseelement)}


def get_query_name(clauseelement: EventClauseElement) -> str:
    # XXX: How to work with other than `str` types of event clause element?
    clauseelement = str(clauseelement)
    # XXX: How to define a query name for `str`?
    query_name = " ".join(clauseelement.split(maxsplit=3)[:3])
    # We want to replace all digits with NUM to avoid cardinality explosion.
    # example of the query: "SAVEPOINT sa_savepoint_33"
    return re.sub(_DIGITS_REGEX, "<NUM>", query_name)


class QueryTotal:
    def __init__(
        self,
        const_labels: ConstCommonLabels,
        query_labels_getter: QueryLabelsGetter = default_query_labels_getter,
        metric: Counter = SRE_DB_QUERY_TOTAL,
    ) -> None:
        self.const_labels = const_labels
        self.query_labels_getter = query_labels_getter
        self.metric = metric

    def on_before_execute(
        self,
        conn: Connection,
        clauseelement: EventClauseElement,
        multiparams: typing.List[typing.Dict[str, typing.Any]],
        params: typing.Dict[str, typing.Any],
        execution_options: typing.Dict[str, typing.Any],
    ) -> None:
        labels = {**self.const_labels, **self.get_event_labels(clauseelement)}
        self.metric.labels(**labels).inc()

    def get_event_labels(
        self, clauseelement: EventClauseElement
    ) -> typing.Dict[str, typing.Any]:
        return {**self.query_labels_getter(clauseelement)}


class QueryTime:
    CONTEXT_KEY = "query_start_time"

    def __init__(
        self,
        const_labels: ConstCommonLabels,
        query_labels_getter: QueryLabelsGetter = default_query_labels_getter,
        metric: Counter = SRE_DB_QUERY_TIME,
    ) -> None:
        self.const_labels = const_labels
        self.query_labels_getter = query_labels_getter
        self.metric = metric

    def on_before_execute(
        self,
        conn: Connection,
        clauseelement: EventClauseElement,
        multiparams: typing.List[typing.Dict[str, typing.Any]],
        params: typing.Dict[str, typing.Any],
        execution_options: typing.Dict[str, typing.Any],
    ) -> None:
        conn.info.setdefault(self.CONTEXT_KEY, []).append(timeit.default_timer())

    def on_after_execute(
        self,
        conn: Connection,
        clauseelement: EventClauseElement,
        multiparams: typing.List[typing.Dict[str, typing.Any]],
        params: typing.Dict[str, typing.Any],
        execution_options: typing.Dict[str, typing.Any],
        result: CursorResult,
    ) -> None:
        labels = {**self.const_labels, **self.get_event_labels(clauseelement)}
        total_sec = timeit.default_timer() - conn.info[self.CONTEXT_KEY].pop(-1)
        self.metric.labels(**labels).inc(total_sec * 1000)

    def on_handle_error(self, exception_context: ExceptionContext) -> None:
        connection = exception_context.connection
        if connection and self.CONTEXT_KEY in connection.info:
            labels = {
                **self.const_labels,
                **self.get_event_labels(
                    _get_clauseelement_from_exception_context(exception_context)
                ),
            }
            total_sec = timeit.default_timer() - connection.info[self.CONTEXT_KEY].pop(
                -1
            )
            self.metric.labels(**labels).inc(total_sec * 1000)

    def get_event_labels(
        self, clauseelement: EventClauseElement
    ) -> typing.Dict[str, typing.Any]:
        return {**self.query_labels_getter(clauseelement)}


class QueryErrorsTotal:
    def __init__(
        self,
        const_labels: ConstCommonLabels,
        query_labels_getter: QueryLabelsGetter = default_query_labels_getter,
        metric: Counter = SRE_DB_QUERY_ERRORS,
    ) -> None:
        self.const_labels = const_labels
        self.query_labels_getter = query_labels_getter
        self.metric = metric

    def on_handle_error(self, exception_context: ExceptionContext) -> None:
        labels = {
            **self.const_labels,
            **self.get_event_labels(
                _get_clauseelement_from_exception_context(exception_context)
            ),
        }
        self.metric.labels(**labels).inc()

    def get_event_labels(self, statement: str) -> typing.Dict[str, typing.Any]:
        return {**self.query_labels_getter(statement)}


# TODO CRYPTO-148: Implement ResponseSize, ResponseRecords


def _get_clauseelement_from_exception_context(
    context: ExceptionContext,
) -> EventClauseElement:
    exec_context = context.execution_context
    if exec_context:
        compiled = getattr(exec_context, "compiled", None)
        if compiled:
            return compiled
    return context.statement or ""
