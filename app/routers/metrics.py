from fastapi import APIRouter
from prometheus_client import REGISTRY, generate_latest
from starlette.responses import PlainTextResponse

router = APIRouter(tags=["common"])


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    description="Application metrics in Prometheus format.",
    responses={
        200: {
            "description": "Metrics",
            "content": {"text/plain": {"example": "<latest prometheus metrics>"}},
        }
    },
)
def get_metrics():
    return generate_latest(REGISTRY)
