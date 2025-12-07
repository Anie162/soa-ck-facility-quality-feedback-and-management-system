from fastapi import FastAPI
from route.reporting_service_route import route as report_router

app = FastAPI()

app.include_router(report_router, prefix="/api")
