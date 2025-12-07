from fastapi import APIRouter, HTTPException, Header, Depends
from model.Report import Report, ReportBase, ReportCreate
from database import reports_collection
from datetime import datetime
import uuid

router = APIRouter()

# --- 1. Hàm phụ trợ để lấy Role từ Header ---
def get_user_role(x_role: str = Header("USER", alias="X-Role")):
    # Mặc định nếu không có header thì coi như là "USER" thường
    return x_role

# Serializer 
def report_serializer(report) -> dict:
    return {
        "id": str(report["_id"]),
        "ReportId": report["ReportId"],
        "Title": report["Title"],
        "Content": report["Content"],
        "MediaURL": report["MediaURL"],
        "Address": report["Address"],
        "Created_at": report["Created_at"],
        "Updated_at": report.get("Updated_at"),
        "Status": report["Status"],
        "Note": report.get("Note"),
        "UserID": report["UserID"],
    }

def get_user_id_from_header(x_user_id: str = Header(..., alias="user-id")):
    return x_user_id

# CREATE 
@router.post("/reports", response_model=dict)
def create_report(report_input: ReportCreate):
    report_data = report_input.dict()
    user_id: str = Depends(get_user_id_from_header)
    report_data["UserID"] = user_id
    report_data["ReportId"] = str(uuid.uuid4())
    report_data["Status"] = "WAITING"
    report_data["Created_at"] = datetime.utcnow()
    report_data["Updated_at"] = None
    result = reports_collection.insert_one(report_data)
    new_report = reports_collection.find_one({"_id": result.inserted_id})
    return {"message": "Report created", "data": report_serializer(new_report)}

# GET ALL 
@router.get("/reports", response_model=list)
def get_all_reports():
    reports = []
    for report in reports_collection.find():
        reports.append(report_serializer(report))
    return reports

# GET Reports by UserID
@router.get("/reports/user/{user_id}", response_model=list)
def get_reports_by_user_id(user_id: str):
    reports = []
    # Tìm tất cả báo cáo có UserID khớp với tham số truyền vào
    cursor = reports_collection.find({"UserID": user_id})
    
    for report in cursor:
        reports.append(report_serializer(report))
        
    # Nếu không tìm thấy báo cáo nào, trả về danh sách rỗng [] (HTTP 200) là chuẩn nhất
    return reports

# GET Report BY ReportID 
@router.get("/reports/{report_id}", response_model=dict)
def get_report_by_id(report_id: str):
    report = reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_serializer(report)

# UPDATE
@router.put("/reports/{report_id}", response_model=dict)
def update_report(
    report_id: str, 
    updated_data: ReportBase,
    role: str = Depends(get_user_role) # <--- Lấy Role của người gọi API
):
    # 1. Lọc bỏ các giá trị None
    update_data_dict = {k: v for k, v in updated_data.dict().items() if v is not None}
    
    if not update_data_dict:
         raise HTTPException(status_code=400, detail="No data provided to update")

    # 2. --- LOGIC PHÂN QUYỀN STATUS ---
    # Kiểm tra: Nếu người dùng cố tình gửi lên trường "Status"
    if "Status" in update_data_dict:
        # Thì bắt buộc Role phải là MANAGER
        if role != "MANAGER":
            raise HTTPException(
                status_code=403, 
                detail="Permission denied: Only MANAGER can update report status."
            )
            # Nếu là MANAGER thì cho qua, code chạy tiếp xuống dưới

    # 3. Cập nhật thời gian
    update_data_dict["Updated_at"] = datetime.utcnow()

    result = reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_data_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Report updated", "data": report_serializer(report)}

# DELETE 
@router.delete("/reports/{report_id}", response_model=dict)
def delete_report(report_id: str):
    result = reports_collection.delete_one({"ReportId": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted"}