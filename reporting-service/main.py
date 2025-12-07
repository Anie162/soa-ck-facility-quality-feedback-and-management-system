from fastapi import FastAPI
from route.reporting_service_route import route as report_router

app = FastAPI(
    title="Reporting Service",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

app.include_router(report_router, prefix="/api/report")
