from fastapi import APIRouter, HTTPException
from model.Report import Report, ReportBase, ReportStatus
from database import reports_collection
from bson import ObjectId
import datetime

router = APIRouter()

# Convert ObjectId → string (MongoDB không cho trả ObjectId trực tiếp)
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

@router.post("/reports", response_model=dict)
async def create_report(report: Report):
    report_dict = report.dict()
    result = await reports_collection.insert_one(report_dict)

    new_report = await reports_collection.find_one({"_id": result.inserted_id})
    return {"message": "Report created", "data": report_serializer(new_report)}


@router.get("/reports", response_model=list)
async def get_all_reports():
    reports = []
    async for report in reports_collection.find():
        reports.append(report_serializer(report))
    return reports


@router.get("/reports/{report_id}", response_model=dict)
async def get_report_by_id(report_id: str):
    report = await reports_collection.find_one({"ReportId": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report_serializer(report)

@router.put("/reports/{report_id}", response_model=dict)
async def update_report(report_id: str, updated_data: ReportBase):
    update_data = {k: v for k, v in updated_data.dict().items() if v is not None}
    update_data["Updated_at"] = datetime.utcnow()

    result = await reports_collection.update_one(
        {"ReportId": report_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    report = await reports_collection.find_one({"ReportId": report_id})
    return {"message": "Report updated", "data": report_serializer(report)}


@router.delete("/reports/{report_id}", response_model=dict)
async def delete_report(report_id: str):
    result = await reports_collection.delete_one({"ReportId": report_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"message": "Report deleted"}
