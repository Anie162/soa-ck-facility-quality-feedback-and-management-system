from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class ReportStatus(str, Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class ReportBase(BaseModel):
    ReportId: str
    Title: str
    Content: str
    MediaURL: str
    Address: str
    Created_at: datetime = Field(default_factory=datetime.utcnow)
    Updated_at: Optional[datetime] = None
    Status: ReportStatus = Field(default=ReportStatus.WAITING)
    Note: Optional[str] = None

class Report(ReportBase):
    UserID: str
