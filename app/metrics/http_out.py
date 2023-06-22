from prometheus_client import Counter, Gauge

from app.metrics.common import location_labels

common_labels = (
    "http_out_host",
    "http_out_port",
    "http_out_method",
    "http_out_url",
    *location_labels,
)

SRE_DNS_TIME = Gauge("http_out_dns_time", "Time spent on DNS resolve", common_labels)

SRE_CONNECT_TIME = Counter(
    "http_out_connect_time_total",
    "Time spent connecting to the remote endpoint",
    common_labels,
)

SRE_HANDSHAKE_TIME = Counter(
    "http_out_handshake_time_total",
    "Time that spends on handshake to the remote endpoint in a case of TLS ",
    common_labels,
)

SRE_REQUEST = Counter(
    "http_out_requests_total",
    "Total amount of outgoing requests on each HTTP connection",
    common_labels,
)

SRE_REQUEST_SIZE = Counter(
    "http_out_request_bytes_total",
    "Size of outgoing request on each HTTP connection",
    common_labels,
)

SRE_REQUEST_ERROR = Counter(
    "http_out_request_errors_total",
    "Amount of errors on outgoing request on each HTTP connection",
    ("http_out_request_error", *common_labels),
)

SRE_RESPONSE = Counter(
    "http_out_responses_total",
    "Amount of errors on outgoing request on each HTTP connection",
    ("http_out_response_code", *common_labels),
)

SRE_RESPONSE_SIZE = Counter(
    "http_out_response_bytes_total",
    "Content length or response size",
    ("http_out_response_code", *common_labels),
)

SRE_RESPONSE_ERROR = Counter(
    "http_out_response_errors_total",
    "Total amount of outgoing errors on each response",
    ("http_out_response_code", "http_out_response_error", *common_labels),
)

SRE_RESPONSE_FIRST_BYTE = Gauge(
    "http_out_response_first_byte_time",
    "Time spent on getting first byte from the remote endpoint",
    ("http_out_response_code", *common_labels),
)

SRE_RESPONSE_TIME = Counter(
    "http_out_response_time_total",
    "Total amount of outgoing errors on each response",
    ("http_out_response_code", *common_labels),
)
