from prometheus_client import Counter, Gauge, Histogram

from app.metrics.common import location_labels

LATENCY_BUCKETS = (
    50,
    100,
    250,
    500,
    750,
    1000,
    2500,
    5000,
    7500,
    10000,
    25000,
    float("inf"),
)

common_labels = (
    "http_in_host",
    "http_in_ip",
    "http_in_port",
    "http_in_method",
    "http_in_url",
    "http_in_source_ip",
    "http_in_source_port",
    *location_labels,
)


class HttpIn:
    _instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, include_latency_histogram: bool = False):
        self.SRE_SERVICE_UPTIME = Gauge(
            "http_in_uptime",
            "Seconds since the HTTP listener has started",
            ("http_in_ip", "http_in_port", "http_in_tier", *location_labels),
            multiprocess_mode="max",
        )

        self.SRE_REQUESTS_TOTAL = Counter(
            "http_in_requests_total", "Total count of requests", common_labels
        )

        self.SRE_REQUEST_BYTES = Counter(
            "http_in_request_bytes", "Total amount of request body size", common_labels
        )

        self.SRE_RESPONSES_TOTAL = Counter(
            "http_in_responses_total",
            "Total count of responses",
            ("http_in_response_code", *common_labels),
        )

        self.SRE_RESPONSE_BYTES = Counter(
            "http_in_response_bytes_total",
            "Total amount of response body size",
            ("http_in_response_code", *common_labels),
        )

        self.SRE_RESPONSE_TIME = Counter(
            "http_in_response_time_total",
            "Total amount of response time",
            ("http_in_response_code", *common_labels),
        )

        if include_latency_histogram:
            self.SRE_RESPONSE_TIME_HISTOGRAM = Histogram(
                "http_in_response_time_histogram",
                "Total amount of response time",
                ("http_in_method", "http_in_url", *location_labels),
                buckets=LATENCY_BUCKETS,
            )

        self.SRE_REQUEST_ERRORS = Counter(
            "http_in_request_errors_total",
            "Total amount of request errors",
            ("http_in_request_error", *common_labels),
        )

        self.SRE_RESPONSE_ERRORS = Counter(
            "http_in_response_errors_total",
            "Total amount of response errors",
            ("http_in_response_code", "http_in_response_error", *common_labels),
        )
