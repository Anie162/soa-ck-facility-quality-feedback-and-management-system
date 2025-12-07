from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from route.reporting_service_route import router as report_router
from route.complaint_route import router as complaint_router

# Định nghĩa mô tả cho từng Tag để Swagger hiện đẹp hơn
tags_metadata = [
    {
        "name": "Reports",
        "description": "Quản lý các báo cáo sự cố hạ tầng (Tạo, Sửa, Duyệt).",
    },
    {
        "name": "Complaints",
        "description": "Quản lý khiếu nại đối với các báo cáo đã hoàn thành.",
    },
]

app = FastAPI(
    title="Reporting Service",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    openapi_tags=tags_metadata
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


app.include_router(
    report_router, 
    prefix="/api/report", 
    tags=["Reports"]  # Gom tất cả API của route này vào nhóm "Reports"
)

app.include_router(
    complaint_router, 
    prefix="/api/complaint", 
    tags=["Complaints"] # Gom tất cả API của route này vào nhóm "Complaints"
)