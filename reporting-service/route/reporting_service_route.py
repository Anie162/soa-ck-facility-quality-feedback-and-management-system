from fastapi import APIRouter, HTTPException, Header, Depends
from model.Report import Report, ReportBase, ReportCreate, ReportStatus, IncidentTypeEnum
from database import reports_collection
from datetime import datetime
import uuid

router = APIRouter()

# Hàm lấy Role từ Header
def get_user_role(x_role: str = Header("USER", alias="X-Role")):
    return x_role

# Hàm lấy UserID từ Header
def get_user_id_from_header(x_user_id: str = Header(..., alias="user-id")):
    return x_user_id

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
        "UserID": report["UserID"],
    }

# CREATE REPORT
@router.post("/reports", response_model=dict)
def create_report(
    report_input: ReportCreate,
    user_id: str = Depends(get_user_id_from_header) 
):
    report_data = report_input.dict()
    
    # 1. TỰ ĐỘNG TẠO TITLE
    # report_input.IncidentType.value sẽ lấy ra chuỗi tiếng Việt (VD: "Hư hỏng đường bộ...")
    auto_title = f"Sự cố hạ tầng - {report_input.IncidentType.value}"
    report_data["Title"] = auto_title
    
    # 2. Điền các thông tin khác
    report_data["UserID"] = user_id
    report_data["ReportId"] = str(uuid.uuid4())
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

# GET ALL 
@router.get("/reports", response_model=list)
def get_all_reports():
    reports = []
    for report in reports_collection.find():
        reports.append(report_serializer(report))
    return reports

# GET REPORTS BY USER ID
@router.get("/reports/user/{user_id}", response_model=list)
def get_reports_by_user_id(user_id: str):
    reports = []
    cursor = reports_collection.find({"UserID": user_id})
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