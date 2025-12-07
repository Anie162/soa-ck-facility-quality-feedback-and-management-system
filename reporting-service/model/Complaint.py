from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 1. Base: Dùng cho update (nếu cần)
class ComplaintBase(BaseModel):
    Content: Optional[str] = None
    Status: Optional[str] = None

# 2. Create: Những gì người dùng cần nhập
class ComplaintCreate(BaseModel):
    ReportId: str  # Bắt buộc phải biết đang khiếu nại cho báo cáo nào
    Content: str   # Lý do khiếu nại (VD: Sửa chưa dứt điểm)
    UserID: str

# 3. Full: Dùng để lưu DB và trả về
class Complaint(ComplaintCreate):
    ComplaintId: str
    Created_at: datetime
    Status: str     # PENDING, RESOLVED...