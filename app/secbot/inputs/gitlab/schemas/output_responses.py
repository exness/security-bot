from typing import List

from pydantic import AnyUrl, BaseModel

from app.secbot.schemas import Severity


class OutputFinding(BaseModel):
    """Base output finding model."""

    title: str
    severity: Severity
    url: AnyUrl


class OutputResponse(BaseModel):
    """Base output response model."""

    project_name: str
    project_url: AnyUrl
    findings: List[OutputFinding]
