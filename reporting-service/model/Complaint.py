from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 1. Base: Dùng cho update
class ComplaintBase(BaseModel):
    Content: Optional[str] = None
    Status: Optional[str] = None

# 2. ComplaintCreate: Input của người dùng
class ComplaintCreate(BaseModel):
    Content: str  

# 3. Complaint
class Complaint(ComplaintCreate):
    ComplaintId: str
    ReportId: str   # Backend tự điền từ URL
    UserID: str     # Backend tự điền từ Header
    Created_at: datetime
    Status: str     # Backend tự điền