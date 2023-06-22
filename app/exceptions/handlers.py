from typing import TYPE_CHECKING, List, Union

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.exceptions.api_errors import APIError
from app.exceptions.schemas import ValidationErrorDetail

if TYPE_CHECKING:
    from pydantic.error_wrappers import ErrorDict


async def api_error_exception_handler(_, starlette_exc: APIError):
    return JSONResponse(starlette_exc.as_dict(), status_code=starlette_exc.status_code)


async def http_exception_handler(_, starlette_exc: HTTPException):
    exc_class = APIError.get_cls_by_code(starlette_exc.status_code)
    exc = exc_class(message=starlette_exc.detail)
    return JSONResponse(exc.as_dict(), status_code=exc.status_code)


async def validation_exception_handler(_, starlette_exc: RequestValidationError):
    exc_class = APIError.get_cls_by_code(400)
    exc = exc_class(
        "VALIDATION_FAILED",
        details=normalize_details(starlette_exc.errors()),
    )
    return JSONResponse(exc.as_dict(), status_code=exc.status_code)


def normalize_details(details: List["ErrorDict"]) -> List[ValidationErrorDetail]:
    res = []
    for data in details:
        field: Union[int, str] = ".".join(
            [loc for loc in data["loc"][2:] if isinstance(loc, str)]
        )
        if not field and isinstance(data["loc"], tuple) and len(data["loc"]) >= 2:
            field = data["loc"][1]

        res.append(
            ValidationErrorDetail(
                code=data["type"].upper(),
                field=field,
                message=data["msg"],
            )
        )
    return res
