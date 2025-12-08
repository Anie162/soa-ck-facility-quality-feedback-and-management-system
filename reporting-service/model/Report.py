from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

# Model cho Địa chỉ
class AddressSchema(BaseModel):
    Detail: str = Field(..., description="Số nhà, ngõ, ngách")
    Street: str = Field(..., description="Tên đường")
    Ward: str = Field(..., description="Phường/Xã")
    District: str = Field(..., description="Quận/Huyện")
    City: str = Field(..., description="Tỉnh/Thành phố")

# Enum trạng thái
class ReportStatus(str, Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

# IncidentType Enum
class IncidentTypeEnum(str, Enum):
    ROAD_DAMAGE = "Hư hỏng đường bộ (Ổ gà, nứt)"
    DRAINAGE = "Ngập úng / Tắc cống thoát nước"
    STREET_LIGHT = "Hỏng đèn chiếu sáng công cộng"
    TRAFFIC_SIGNAL = "Hỏng đèn tín hiệu / Biển báo"
    SIDEWALK = "Hư hỏng vỉa hè / Lấn chiếm"
    WATER_LEAK = "Vỡ ống nước / Rò rỉ nước sạch"
    FALLEN_TREE = "Cây xanh gãy đổ"
    GARBAGE = "Rác thải ùn ứ / Môi trường"
    MANHOLE = "Mất hoặc hỏng nắp hố ga"
    PUBLIC_FACILITY = "Hư hỏng công trình công cộng khác"
    OTHER = "Sự cố khác" 
    
# ReportBase: Dùng cho việc UPDATE (PUT)
class ReportBase(BaseModel):
    # Cho phép Admin sửa lại loại sự cố nếu người dân chọn sai
    IncidentType: Optional[IncidentTypeEnum] = None 
    Content: Optional[str] = None
    MediaURL: Optional[str] = None
    Address: Optional[AddressSchema] = None
    Note: Optional[str] = None
    Status: Optional[ReportStatus] = None

# ReportCreate: Dùng cho việc CREATE (POST)
class ReportCreate(BaseModel):
    IncidentType: IncidentTypeEnum = Field(..., description="Chọn loại sự cố")
    Content: str
    MediaURL: str  # Bắt buộc
    Address: AddressSchema   # Bắt buộc 

# Report: Dùng cho việc RESPONSE (GET)
class Report(ReportCreate):
    ReportId: str
    Title: str
    Status: ReportStatus = Field(default=ReportStatus.WAITING) 
    Created_at: datetime
    Updated_at: Optional[datetime] = None
    Note: Optional[str] = None
    UserID: str