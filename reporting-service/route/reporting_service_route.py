from fastapi import APIRouter, HTTPException, Header, Depends, Query
from model.Report import Report, ReportBase, ReportCreate, ReportStatus, IncidentTypeEnum
from database import reports_collection
from datetime import datetime
from typing import Optional
import uuid

router = APIRouter()

# ! CALL USER SERVICE TO VERIFY USER (UserID)
# Hàm lấy Role từ Header
def get_user_role(x_role: str = Header("USER", alias="X-Role")):
    return x_role

# Hàm lấy UserID từ Header
def get_user_id_from_header(x_user_id: str = Header(..., alias="user-id")):
    return x_user_id
## ---- ##

# Serializer 
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
        "ReporterID": report["UserID"],               # Người báo cáo
        "ManagerID": report.get("ManagerID"),         # Người điều phối
        "TechnicianID": report.get("TechnicianID"),   # Người xử lý
    }

# CREATE REPORT
@router.post("/reports", response_model=dict)
def create_report(
    report_input: ReportCreate,
    user_id: str = Depends(get_user_id_from_header) 
):
    report_data = report_input.dict()
    
    # 1. Tự động tạo Title (Giữ nguyên logic cũ)
    auto_title = f"Sự cố hạ tầng - {report_input.IncidentType.value}"
    report_data["Title"] = auto_title
    
    # 2. LOGIC TẠO ID MỚI: RP + UserID + Số thứ tự (01, 02...)
    # Đếm số báo cáo hiện có của User này
    current_count = reports_collection.count_documents({"UserID": user_id})
    
    # Tăng lên 1
    next_seq = current_count + 1
    
    # Format số thứ tự thành 2 chữ số (vd: 1 -> 01, 9 -> 09, 10 -> 10)
    # f"{next_seq:02d}" là số nguyên, đệm số 0 cho đủ 2 ký tự
    report_id = f"RP{user_id}{next_seq:02d}"
    
    report_data["ReportId"] = report_id  # Gán ID mới vào
    report_data["UserID"] = user_id
    report_data["Status"] = "WAITING"
    report_data["Created_at"] = datetime.utcnow()
    report_data["Updated_at"] = None
    
    result = reports_collection.insert_one(report_data)
    new_report = reports_collection.find_one({"_id": result.inserted_id})
    return {"message": "Report created", "data": report_serializer(new_report)}

# Cập nhật cả Title nếu đổi loại sự cố
@router.put("/reports/{report_id}", response_model=dict)
def update_report(
    report_id: str, 
    updated_data: ReportBase,
    role: str = Depends(get_user_role)
):
    update_data_dict = {k: v for k, v in updated_data.dict().items() if v is not None}
    
    if not update_data_dict:
         raise HTTPException(status_code=400, detail="No data provided to update")

    if "Status" in update_data_dict and role != "MANAGER":
         raise HTTPException(status_code=403, detail="Permission denied: Only MANAGER can update status.")

    # Nếu Admin đổi IncidentType, thì phải đổi luôn Title cho khớp
    if "IncidentType" in update_data_dict:
        # Lấy giá trị Enum từ string gửi lên
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


@router.get("/reports", response_model=list)
def get_reports(
    # 1. Lọc theo 3 Vai Trò
    reporter_id: Optional[str] = Query(None, description="Lọc theo ID người báo cáo (Reporter)"),
    manager_id: Optional[str] = Query(None, description="Lọc theo ID người điều phối (Manager)"),
    technician_id: Optional[str] = Query(None, description="Lọc theo ID người xử lý (Technician)"),

    # 2. Lọc theo thuộc tính khác
    status: Optional[ReportStatus] = Query(None, description="Lọc theo trạng thái"),
    incident_type: Optional[IncidentTypeEnum] = Query(None, description="Lọc theo loại sự cố"),
    
    # 3. Lọc theo địa chỉ
    city: Optional[str] = Query(None, description="Lọc theo Thành phố"),
    district: Optional[str] = Query(None, description="Lọc theo Quận/Huyện"),
    ward: Optional[str] = Query(None, description="Lọc theo Phường/Xã"),

    # 4. Lọc theo thời gian
    start_date: Optional[datetime] = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Đến ngày (YYYY-MM-DD)")
):
    # Khởi tạo query
    query = {}

    # --- MAP QUERY PARAM VÀO DATABASE FIELD ---
    if reporter_id:
        query["UserID"] = reporter_id       # Tìm theo UserID
        
    if manager_id:
        query["ManagerID"] = manager_id     # Tìm theo ManagerID
        
    if technician_id:
        query["TechnicianID"] = technician_id # Tìm theo TechnicianID

    # Các bộ lọc khác
    if status:
        query["Status"] = status
    if incident_type:
        query["IncidentType"] = incident_type

    # Lọc địa chỉ (Nested Object)
    if city:
        query["Address.City"] = city
    if district:
        query["Address.District"] = district
    if ward:
        query["Address.Ward"] = ward

    # Lọc thời gian
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["Created_at"] = date_filter

    # Thực hiện truy vấn
    reports = []
    # Sort: Mới nhất lên đầu
    cursor = reports_collection.find(query).sort("Created_at", -1)
    
    for report in cursor:
        reports.append(report_serializer(report))
        
    return reports

# GET REPORTS BY REPORT ID 
@router.get("/reports/{report_id}", response_model=dict)
def get_report_by_id(report_id: str):
    report = reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_serializer(report)

# UPDATE STATUS (MANAGER) - CÓ THỂ KÈM GHI CHÚ
@router.patch("/reports/{report_id}/status", response_model=dict)
def update_report_status(
    report_id: str, 
    status: ReportStatus, # Trạng thái mới (VD: REJECTED)
    note: Optional[str] = Query(None, description="Ghi chú lý do (nếu từ chối/duyệt)"), # <--- THÊM THAM SỐ NÀY
    role: str = Depends(get_user_role)
):
    # 1. Kiểm tra quyền Manager
    if role != "MANAGER":
        raise HTTPException(status_code=403, detail="Permission denied: Only MANAGER can update report status.")

    # 2. Chuẩn bị dữ liệu update
    update_fields = {
        "Status": status,
        "Updated_at": datetime.utcnow()
    }
    
    # Nếu có ghi chú thì cập nhật thêm, không thì thôi
    if note:
        update_fields["Note"] = note

    # 3. Thực hiện update
    result = reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Status updated successfully", "data": report_serializer(report)}

# UPDATE STATUS ONLY (MANAGER)
@router.patch("/reports/{report_id}/status", response_model=dict)
def update_report_status(
    report_id: str, 
    status: ReportStatus, 
    role: str = Depends(get_user_role)
):
    if role != "MANAGER":
        raise HTTPException(status_code=403, detail="Permission denied: Only MANAGER can update report status.")

    result = reports_collection.update_one(
        {"ReportId": report_id},
        {
            "$set": {
                "Status": status,
                "Updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Status updated successfully", "data": report_serializer(report)}

# DELETE
@router.delete("/reports/{report_id}", response_model=dict)
def delete_report(report_id: str):
    result = reports_collection.delete_one({"ReportId": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}