from typing import Dict, List, Optional, Type

from app.exceptions.schemas import ValidationError, ValidationErrorDetail


class APIError(Exception):
    status_code = 500
    default_code = "SERVER_ERROR"
    default_message = "A server error occurred."

    _registry: Dict[int, Type["APIError"]] = {}

    def __init_subclass__(cls, register: bool = False, **kwargs):
        if register is True:
            cls._registry[cls.status_code] = cls
        super().__init_subclass__(**kwargs)  # type: ignore

    def __init__(
        self,
        code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[List[ValidationErrorDetail]] = None,
    ):
        self.info = ValidationError(
            code=code or self.default_code,
            message=message or self.default_message,
            details=details,
        )
        super().__init__()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"code='{self.info.code}',"
            f" message='{self.info.message}',"
            f" details={self.info.details}"
            f")"
        )

    @classmethod
    def get_cls_by_code(cls, status_code: int) -> Type["APIError"]:
        return cls._registry.get(status_code, APIError)

    def as_dict(self):
        return self.info.dict()


class BadRequest(APIError, register=True):
    status_code = 400
    default_code = "BAD_REQUEST"
    default_message = "Bad request."


class Unauthorized(APIError, register=True):
    status_code = 401
    default_code = "UNAUTHORIZED"
    default_message = "Unauthorized."


class PaymentRequired(APIError, register=True):
    status_code = 402
    default_code = "PAYMENT_REQUIRED"
    default_message = "Payment required."


class Forbidden(APIError, register=True):
    status_code = 403
    default_code = "FORBIDDEN"
    default_message = "Forbidden."


class NotFound(APIError, register=True):
    status_code = 404
    default_code = "NOT_FOUND"
    default_message = "Not found."


class MethodNotAllowed(APIError, register=True):
    status_code = 405
    default_code = "METHOD_NOT_ALLOWED"
    default_message = "Method not allowed."


class NotAcceptable(APIError, register=True):
    status_code = 406
    default_code = "NOT_ACCEPTABLE"
    default_message = "Not acceptable."


class ProxyAuthenticationRequired(APIError, register=True):
    status_code = 407
    default_code = "PROXY_AUTHENTICATION_REQUIRED"
    default_message = "Proxy authentication required."


class RequestTimeout(APIError, register=True):
    status_code = 408
    default_code = "REQUEST_TIMEOUT"
    default_message = "Request timeout."


class Conflict(APIError, register=True):
    status_code = 409
    default_code = "CONFLICT"
    default_message = "Conflict."


class Gone(APIError, register=True):
    status_code = 410
    default_code = "GONE"
    default_message = "Gone."


class LengthRequired(APIError, register=True):
    status_code = 411
    default_code = "LENGTH_REQUIRED"
    default_message = "Length required."


class PreconditionFailed(APIError, register=True):
    status_code = 412
    default_code = "PRECONDITION_FAILED"
    default_message = "Precondition failed."


class RequestEntityTooLarge(APIError, register=True):
    status_code = 413
    default_code = "REQUEST_ENTITY_TOO_LARGE"
    default_message = "Request entity too large."


class RequestURITooLong(APIError, register=True):
    status_code = 414
    default_code = "REQUEST_URI_TOO_LONG"
    default_message = "Request URI too long."


class UnsupportedMediaType(APIError, register=True):
    status_code = 415
    default_code = "UNSUPPORTED_MEDIA_TYPE"
    default_message = "Unsupported media type."


class RequestRangeNotSatisfiable(APIError, register=True):
    status_code = 416
    default_code = "REQUEST_RANGE_NOT_SATISFIABLE"
    default_message = "Request range not satisfiable."


class ExpectationFailed(APIError, register=True):
    status_code = 417
    default_code = "EXPECTATION_FAILED"
    default_message = "Expectation failed."


class IAmTeapot(APIError, register=True):
    status_code = 418
    default_code = "I_AM_A_TEAPOT"
    default_message = "I'm a teapot."


class EnhanceYourCalm(APIError, register=True):
    status_code = 420
    default_code = "ENHANCE_YOUR_CALM"
    default_message = "Enhance your calm."


class Misdirected(APIError, register=True):
    status_code = 421
    default_code = "MISDIRECTED"
    default_message = "The server is not able to produce a response."


class UnprocessableEntity(APIError, register=True):
    status_code = 422
    default_code = "UNPROCESSABLE_ENTITY"
    default_message = "Unprocessable entity."


class Locked(APIError, register=True):
    status_code = 423
    default_code = "LOCKED"
    default_message = "Locked."


class FailedDependency(APIError, register=True):
    status_code = 424
    default_code = "FAILED_DEPENDENCY"
    default_message = "Failed dependency."


class ReservedForWebDAV(APIError, register=True):
    status_code = 425
    default_code = "RESERVED_FOR_WEBDAV"
    default_message = "Reserved for WebDAV."


class UpgradeRequired(APIError, register=True):
    status_code = 426
    default_code = "UPGRADE_REQUIRED"
    default_message = "Upgrade required."


class PreconditionRequired(APIError, register=True):
    status_code = 428
    default_code = "PRECONDITION_REQUIRED"
    default_message = "Precondition required."


class TooManyRequests(APIError, register=True):
    status_code = 429
    default_code = "TOO_MANY_REQUESTS"
    default_message = "Too many requests."


class RequestHeaderFieldsTooLarge(APIError, register=True):
    status_code = 431
    default_code = "REQUEST_HEADER_FIELDS_TOO_LARGE"
    default_message = "Request header fields too large."


class UnavailableForLegalReasons(APIError, register=True):
    status_code = 451
    default_code = "UNAVAILABLE_FOR_LEGAL_REASONS"
    default_message = "Unavailable for legal reasons."


class ClientClosedRequest(APIError, register=True):
    status_code = 499
    default_code = "CLIENT_CLOSED_REQUEST"
    default_message = "Client closed request (nginx)."


class InternalServerError(APIError, register=True):
    status_code = 500
    default_code = "INTERNAL_SERVER_ERROR"
    default_message = "The server encountered an unexpected condition."


class ServerNotImplemented(APIError, register=True):
    status_code = 501
    default_code = "NOT_IMPLEMENTED"
    default_message = "Not implemented."


class BadGateway(APIError, register=True):
    status_code = 502
    default_code = "BAD_GATEWAY"
    default_message = "Bad gateway."


class Unavailable(APIError, register=True):
    status_code = 503
    default_code = "SERVICE_UNAVAILABLE"
    default_message = "Service is unavailable."


class GatewayTimeout(APIError, register=True):
    status_code = 504
    default_code = "GATEWAY_TIMEOUT"
    default_message = "Gateway timeout."


class HTTPVersionNotSupported(APIError, register=True):
    status_code = 505
    default_code = "HTTP_VERSION_NOT_SUPPORTED"
    default_message = "HTTP version not supported."


class VariantAlsoNegotiates(APIError, register=True):
    status_code = 506
    default_code = "VARIANT_ALSO_NEGOTIATES"
    default_message = "Variant also negotiates."


class InsufficientStorage(APIError, register=True):
    status_code = 507
    default_code = "INSUFFICIENT_STORAGE"
    default_message = "Insufficient storage."


class LoopDetected(APIError, register=True):
    status_code = 508
    default_code = "LOOP_DETECTED"
    default_message = "Loop detected."


class NotExtended(APIError, register=True):
    status_code = 510
    default_code = "NOT_EXTENDED"
    default_message = "Not extended."


class NetworkAuthenticationRequired(APIError, register=True):
    status_code = 511
    default_code = "NETWORK_AUTHENTICATION_REQUIRED"
    default_message = "Network authentication required."


class NetworkReadTimeoutError(APIError, register=True):
    status_code = 598
    default_code = "NETWORK_READ_TIMEOUT_ERROR"
    default_message = "Network read timeout error."


class NetworkConnectTimeoutError(APIError, register=True):
    status_code = 599
    default_code = "NETWORK_CONNECT_TIMEOUT_ERROR"
    default_message = "Network connect timeout error."
