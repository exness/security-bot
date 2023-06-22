from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["common"])


class PingReplyModel(BaseModel):
    ping: str = "pong"


@router.get("/ping", response_model=PingReplyModel)
def get_ping():
    """Healthcheck for L7 load balancers."""
    return PingReplyModel()
