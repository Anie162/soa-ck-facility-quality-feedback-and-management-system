from fastapi import APIRouter, HTTPException, Header, Depends, Query
from model.Report import Report, ReportBase, ReportCreate, ReportStatus, IncidentTypeEnum
from database import reports_collection
from datetime import datetime
from typing import Optional
import uuid

router = APIRouter()

# --- AUTH HELPERS ---
def get_user_role(x_role: str = Header("USER", alias="X-Role")):
    return x_role

def get_user_id_from_header(x_user_id: str = Header(..., alias="user-id")):
    return x_user_id

# --- SERIALIZER ---
def report_serializer(report) -> dict:
    return {
        "id": str(report["_id"]),
        "ReportId": report["ReportId"],
        "Title": report["Title"],
        "IncidentType": report.get("IncidentType"), 
        "Content": report.get("Content"),
        "MediaURL": report["MediaURL"],
        "Address": report["Address"],
        "Created_at": report["Created_at"],
        "Updated_at": report.get("Updated_at"),
        "Status": report["Status"],
        "Note": report.get("Note"),
        "ReporterID": report["UserID"]
    }

# --- CREATE REPORT ---
@router.post("/reports", response_model=dict)
def create_report(
    report_input: ReportCreate,
    user_id: str = Depends(get_user_id_from_header) 
):
    report_data = report_input.dict()
    auto_title = f"Sự cố hạ tầng - {report_input.IncidentType.value}"
    report_data["Title"] = auto_title
    
    current_count = reports_collection.count_documents({"UserID": user_id})
    next_seq = current_count + 1
    report_id = f"RP{user_id}{next_seq:02d}"
    
    report_data["ReportId"] = report_id
    report_data["UserID"] = user_id
    report_data["Status"] = "WAITING"
    report_data["Created_at"] = datetime.utcnow()
    report_data["Updated_at"] = None
    
    result = reports_collection.insert_one(report_data)
    new_report = reports_collection.find_one({"_id": result.inserted_id})
    return {"message": "Report created", "data": report_serializer(new_report)}

# --- UPDATE REPORT DETAILS (PUT) ---
# Dùng để sửa nội dung (Title, Content, Address...) -> TECHNICIAN KHÔNG ĐƯỢC DÙNG
@router.put("/reports/{report_id}", response_model=dict)
def update_report(
    report_id: str, 
    updated_data: ReportBase,
    role: str = Depends(get_user_role)
):
    # 1. CHẶN TECHNICIAN
    if role == "TECHNICIAN":
        raise HTTPException(
            status_code=403, 
            detail="Permission denied: Technicians cannot modify report details. Please contact Manager."
        )

    # 2. Xử lý dữ liệu
    update_data_dict = {k: v for k, v in updated_data.dict().items() if v is not None}
    if not update_data_dict:
         raise HTTPException(status_code=400, detail="No data provided to update")

    # 3. Chặn sửa Status ở endpoint này (trừ Manager)
    if "Status" in update_data_dict and role != "MANAGER":
         raise HTTPException(status_code=403, detail="Permission denied: Only MANAGER can update status via this endpoint.")

    if "IncidentType" in update_data_dict:
        new_type_enum = updated_data.IncidentType 
        new_title = f"Sự cố hạ tầng - {new_type_enum.value}"
        update_data_dict["Title"] = new_title

    update_data_dict["Updated_at"] = datetime.utcnow()

    result = reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_data_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Report updated", "data": report_serializer(report)}

# --- UPDATE STATUS & NOTE (PATCH) ---
# Dùng cho quy trình xử lý: Manager duyệt, Technician báo cáo xong
@router.patch("/reports/{report_id}/status", response_model=dict)
def update_report_status(
    report_id: str, 
    status: ReportStatus, 
    note: Optional[str] = Query(None, description="Ghi chú lý do"), 
    role: str = Depends(get_user_role)
):
    # 1. Kiểm tra quyền: Chỉ MANAGER và TECHNICIAN mới được update tiến độ
    if role not in ["MANAGER", "TECHNICIAN"]:
        raise HTTPException(status_code=403, detail="Permission denied.")

    # 2. Logic dành riêng cho MANAGER (Reject bắt buộc có Note)
    if role == "MANAGER":
        if status == ReportStatus.REJECTED and not note:
            raise HTTPException(
                status_code=400, 
                detail="Manager must provide a reason (Note) when rejecting a report."
            )

    # 3. Thực hiện update
    update_fields = {
        "Status": status,
        "Updated_at": datetime.utcnow()
    }
    
    if note:
        update_fields["Note"] = note

    result = reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Status updated successfully", "data": report_serializer(report)}

# --- GET ALL & FILTER ---
@router.get("/reports", response_model=list)
def get_reports(
    caller_id: str = Depends(get_user_id_from_header),
    caller_role: str = Depends(get_user_role),
    
    reporter_id: Optional[str] = Query(None),
    status: Optional[ReportStatus] = Query(None),
    incident_type: Optional[IncidentTypeEnum] = Query(None),
    city: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    ward: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    query = {}

    # Logic phân quyền xem
    if caller_role in ["MANAGER", "TECHNICIAN"]:
        # Manager và Technician được xem tất cả
        if reporter_id: query["UserID"] = reporter_id
    else:
        # User thường chỉ xem của mình
        query["UserID"] = caller_id 

    # Các bộ lọc khác
    if status: query["Status"] = status
    if incident_type: query["IncidentType"] = incident_type
    if city: query["Address.City"] = city
    if district: query["Address.District"] = district
    if ward: query["Address.Ward"] = ward

    if start_date or end_date:
        date_filter = {}
        if start_date: date_filter["$gte"] = start_date
        if end_date: date_filter["$lte"] = end_date
        if date_filter: query["Created_at"] = date_filter

    reports = []
    cursor = reports_collection.find(query).sort("Created_at", -1)
    for report in cursor:
        reports.append(report_serializer(report))
    return reports

# --- GET DETAIL ---
@router.get("/reports/{report_id}", response_model=dict)
def get_report_by_id(report_id: str):
    report = reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_serializer(report)

# --- DELETE ---
@router.delete("/reports/{report_id}", response_model=dict)
def delete_report(report_id: str):
    result = reports_collection.delete_one({"ReportId": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}