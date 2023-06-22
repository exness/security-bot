from typing import List, Optional

from pydantic import BaseModel


class ValidationErrorDetail(BaseModel):
    code: str
    field: str
    message: str


class ValidationError(BaseModel):
    code: Optional[str] = None
    message: Optional[str] = None
    details: Optional[List[ValidationErrorDetail]] = None
