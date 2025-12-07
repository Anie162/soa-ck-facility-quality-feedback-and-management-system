from fastapi import APIRouter, HTTPException
from model.Report import Report, ReportBase
from database import reports_collection
from datetime import datetime

router = APIRouter()

# Convert ObjectId -> string
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

# --- LƯU Ý: Đã xóa toàn bộ 'async' và 'await' để tương thích với PyMongo ---

@router.post("/reports", response_model=dict)
def create_report(report: Report):
    report_dict = report.dict()
    # Thêm timestamp nếu chưa có
    if not report_dict.get("Created_at"):
        report_dict["Created_at"] = datetime.utcnow()
        
    result = reports_collection.insert_one(report_dict)
    new_report = reports_collection.find_one({"_id": result.inserted_id})
    return {"message": "Report created", "data": report_serializer(new_report)}


@router.get("/reports", response_model=list)
def get_all_reports():
    reports = []
    # Dùng vòng lặp thường, KHÔNG dùng async for
    for report in reports_collection.find():
        reports.append(report_serializer(report))
    return reports


@router.get("/reports/{report_id}", response_model=dict)
def get_report_by_id(report_id: str):
    report = reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_serializer(report)


@router.put("/reports/{report_id}", response_model=dict)
def update_report(report_id: str, updated_data: ReportBase):
    # Lọc bỏ các giá trị None
    update_data_dict = {k: v for k, v in updated_data.dict().items() if v is not None}
    
    if not update_data_dict:
         raise HTTPException(status_code=400, detail="No data provided to update")

    update_data_dict["Updated_at"] = datetime.utcnow()

    result = reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_data_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = reports_collection.find_one({"ReportId": report_id})
    return {"message": "Report updated", "data": report_serializer(report)}


@router.delete("/reports/{report_id}", response_model=dict)
def delete_report(report_id: str):
    result = reports_collection.delete_one({"ReportId": report_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"message": "Report deleted"}