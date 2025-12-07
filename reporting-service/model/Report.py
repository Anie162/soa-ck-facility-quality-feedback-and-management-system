from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

# 1. Enum trạng thái (Giữ nguyên)
class ReportStatus(str, Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

# 2. ReportBase: Dùng cho việc UPDATE (PUT)
class ReportBase(BaseModel):
    Title: Optional[str] = None
    Content: Optional[str] = None
    MediaURL: Optional[str] = None
    Address: Optional[str] = None
    Note: Optional[str] = None
    Status: Optional[ReportStatus] = None 

# 3. ReportCreate: Dùng cho việc CREATE (POST)
# Đây là những trường người dùng BẮT BUỘC phải nhập
class ReportCreate(BaseModel):
    Title: str
    Content: str
    MediaURL: str  # Bắt buộc
    Address: str   # Bắt buộc 

# 4. Report: Dùng cho việc RESPONSE (GET)
class Report(ReportCreate):
    ReportId: str
    Status: ReportStatus = Field(default=ReportStatus.WAITING) 
    Created_at: datetime
    Updated_at: Optional[datetime] = None
    Note: Optional[str] = None
    UserID: str