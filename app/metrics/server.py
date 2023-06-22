import os
import timeit
from typing import Any, Dict

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.types import ASGIApp

from app.exceptions.api_errors import APIError
from app.metrics.common import get_location_labels_from_env
from app.metrics.constants import PROMETHEUS_MULTIPROC_DIR
from app.metrics.http_in import HttpIn


class ASGIMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        tier: int = 1,
        include_latency_histogram=False,
        record_source_ip=False,
        record_source_port=False,
        include_not_found_url_label=True,
    ):
        super().__init__(app)
        self.include_latency_histogram = include_latency_histogram
        self.http_in = HttpIn.get_instance(include_latency_histogram)
        self.tier = tier
        self.start_time = timeit.default_timer()
        self.record_source_ip = record_source_ip
        self.record_source_port = record_source_port
        self.include_not_found_url_label = include_not_found_url_label

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_start_time = (
            timeit.default_timer()
        )  # TODO depends on the order of the middleware
        common_labels = self.get_common_labels(request)
        self.observe_uptime(request)
        self.observe_request(request, common_labels)
        response_content_length = 0
        status_code = ""
        error_message = ""

        try:
            response = await call_next(request)
        except Exception as e:
            status_code = 500
            response_content_length = 0
            error_message = "Unhandled exception"
            raise e from None
        else:
            status_code = response.status_code
            response_content_length = int(response.headers.get("content-length", "0"))
            # I was unable to find a satisfactory way to obtain a detailed error message
            # falling back to the default message based on the status code
            error_message = APIError.get_cls_by_code(status_code).default_message
        finally:
            latency = int((timeit.default_timer() - request_start_time) * 1000)
            self.observe_response(
                common_labels,
                latency,
                status_code,
                response_content_length,
                error_message,
            )

        return response

    def observe_response(
        self,
        labels: Dict[str, Any],
        latency: int,
        status_code: int,
        content_length: int,
        error_message: str,
    ):
        response_labels = {
            **labels,
            "http_in_response_code": status_code,
        }

        if status_code >= 400:
            self.http_in.SRE_RESPONSE_ERRORS.labels(
                **{**response_labels, "http_in_response_error": error_message}
            ).inc()

        self.http_in.SRE_RESPONSE_BYTES.labels(**response_labels).inc(content_length)
        self.http_in.SRE_RESPONSE_TIME.labels(**response_labels).inc(latency)
        if self.include_latency_histogram:
            self.http_in.SRE_RESPONSE_TIME_HISTOGRAM.labels(
                http_in_method=response_labels.get("http_in_method", ""),
                http_in_url=response_labels.get("http_in_url", ""),
                **get_location_labels_from_env(),
            ).observe(latency)
        self.http_in.SRE_RESPONSES_TOTAL.labels(**response_labels).inc()

    def observe_request(self, request: Request, labels: Dict[str, Any]):
        content_length = int(request.headers.get("content-length", "0"))
        self.http_in.SRE_REQUESTS_TOTAL.labels(**labels).inc()
        self.http_in.SRE_REQUEST_BYTES.labels(**labels).inc(content_length)

    def observe_uptime(self, request: Request):
        http_in_ip, http_in_port = request.get("server")
        uptime = timeit.default_timer() - self.start_time
        self.http_in.SRE_SERVICE_UPTIME.labels(
            **{
                **self.get_location_labels(),
                "http_in_ip": http_in_ip,
                "http_in_port": http_in_port,
                "http_in_tier": self.tier,
            }
        ).set(uptime)

    def get_location_labels(self) -> Dict[str, str]:
        return get_location_labels_from_env()

    def get_common_labels(self, request: Request) -> Dict[str, Any]:
        path_template = self.get_path_template(request)
        http_in_ip, http_in_port = request.get("server")
        client_host = request.client.host
        client_port = request.client.port

        return {
            **self.get_location_labels(),
            "http_in_host": request.base_url.hostname,
            "http_in_ip": http_in_ip,
            "http_in_port": http_in_port,
            "http_in_method": request.method,
            "http_in_url": path_template,
            "http_in_source_ip": client_host if self.record_source_ip else "",
            "http_in_source_port": client_port if self.record_source_port else "",
        }

    def get_path_template(self, request: Request) -> str:
        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match in (Match.FULL, Match.PARTIAL):
                return route.path

        if self.include_not_found_url_label:
            return request.url.path

        return "-"


async def metrics_handler(request: Request):
    if (
        PROMETHEUS_MULTIPROC_DIR in os.environ
        or PROMETHEUS_MULTIPROC_DIR.lower() in os.environ
    ):
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    return Response(
        generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )
