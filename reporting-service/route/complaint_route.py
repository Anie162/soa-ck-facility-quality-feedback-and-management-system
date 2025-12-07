from fastapi import APIRouter, HTTPException
from model.Complaint import Complaint, ComplaintCreate
from database import complaints_collection, reports_collection
from datetime import datetime
import uuid

router = APIRouter()

# Serializer
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

# TẠO KHIẾU NẠI
@router.post("/complaints", response_model=dict)
def create_complaint(complaint_input: ComplaintCreate):
    # 1. Tìm cái Report gốc xem có tồn tại không
    report = reports_collection.find_one({"ReportId": complaint_input.ReportId})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report ID not found")

    # 2. CHECK LOGIC: Chỉ cho phép khiếu nại khi Report đã COMPLETED
    # Nếu chưa xong mà khiếu nại thì vô lý
    if report["Status"] != "COMPLETED":
        raise HTTPException(
            status_code=400, 
            detail="You can only file a complaint for COMPLETED reports."
        )

    # 3. Chuẩn bị dữ liệu Khiếu nại
    complaint_data = complaint_input.dict()
    complaint_data["ComplaintId"] = str(uuid.uuid4())
    complaint_data["Created_at"] = datetime.utcnow()
    complaint_data["Status"] = "PENDING" # Mặc định là đang chờ xử lý

    # 4. Lưu khiếu nại vào DB
    complaints_collection.insert_one(complaint_data)

    # Tự động chuyển trạng thái Report gốc từ COMPLETED -> IN_PROGRESS
    # Để nhân viên thấy và đi sửa lại.
    reports_collection.update_one(
        {"ReportId": complaint_input.ReportId},
        {
            "$set": {
                "Status": "IN_PROGRESS", 
                "Updated_at": datetime.utcnow(),
                "Note": f"Re-opened due to complaint: {complaint_input.Content}"
            }
        }
    )

    return {"message": "Complaint submitted. Report has been re-opened.", "data": complaint_data}

# LẤY DANH SÁCH KHIẾU NẠI CỦA 1 REPORT
@router.get("/complaints/{report_id}", response_model=list)
def get_complaints_by_report(report_id: str):
    complaints = []
    # Tìm tất cả khiếu nại có ReportId trùng khớp
    for c in complaints_collection.find({"ReportId": report_id}):
        complaints.append(complaint_serializer(c))
    return complaints