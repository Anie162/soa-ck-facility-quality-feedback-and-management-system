from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from route.reporting_service_route import router as report_router
from route.complaint_route import router as complaint_router

app = FastAPI(
    title="Reporting Service",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

app.include_router(report_router, prefix="/api/report")
app.include_router(complaint_router, prefix="/api/complaint")
