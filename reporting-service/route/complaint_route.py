from fastapi import APIRouter, HTTPException, Header, Depends
from model.Complaint import Complaint, ComplaintCreate
# Import reports_collection để check trạng thái báo cáo gốc
from database import complaints_collection, reports_collection
from datetime import datetime
import uuid

router = APIRouter()

# ! CALL USER SERVICE TO VERIFY USER (UserID)
# Hàm lấy UserID từ Header
def get_user_id_from_header(x_user_id: str = Header(..., alias="user-id")):
    return x_user_id
## ---- ##

def complaint_serializer(complaint) -> dict:
    return {
        "id": str(complaint["_id"]),
        "ComplaintId": complaint["ComplaintId"],
        "ReportId": complaint["ReportId"],
        "Content": complaint["Content"],
        "Status": complaint["Status"],
        "Created_at": complaint["Created_at"],
        "UserID": complaint["UserID"]
    }

# TẠO KHIẾU NẠI DỰA TRÊN REPORT ID TRÊN URL
# URL sẽ có dạng: /api/complaint/report/R-123456
@router.post("/report/{report_id}", response_model=dict)
def create_complaint(
    report_id: str,   # Lấy ID từ URL
    complaint_input: ComplaintCreate, # Lấy nội dung từ Body
    user_id: str = Depends(get_user_id_from_header) # Lấy User từ Header
):
    # 1. Kiểm tra Report có tồn tại không
    report = reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report ID not found")

    # 2. Chỉ cho khiếu nại khi báo cáo đã Xong 
    if report["Status"] != "COMPLETED":
        raise HTTPException(
            status_code=400, 
            detail="You can only file a complaint for COMPLETED reports."
        )

    # 3. Chuẩn bị dữ liệu để lưu
    complaint_data = complaint_input.dict()
    complaint_data["ComplaintId"] = str(uuid.uuid4())
    complaint_data["ReportId"] = report_id # Gán ID từ URL vào data
    complaint_data["UserID"] = user_id     # Gán ID từ Header vào data
    complaint_data["Created_at"] = datetime.utcnow()
    complaint_data["Status"] = "PENDING"

    # 4. Lưu Complaint
    complaints_collection.insert_one(complaint_data)

    # 5. Tự động mở lại Report
    # Chuyển trạng thái Report từ COMPLETED -> IN_PROGRESS
    reports_collection.update_one(
        {"ReportId": report_id},
        {
            "$set": {
                "Status": "IN_PROGRESS",
                "Updated_at": datetime.utcnow(),
                "Note": f"Re-opened due to complaint: {complaint_input.Content}"
            }
        }
    )

    return {"message": "Complaint submitted successfully", "data": complaint_data}

# Lấy danh sách khiếu nại của 1 report
@router.get("/report/{report_id}", response_model=list)
def get_complaints_by_report(report_id: str):
    complaints = []
    for c in complaints_collection.find({"ReportId": report_id}):
        complaints.append(complaint_serializer(c))
    return complaints