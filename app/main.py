from fastapi import FastAPI
from app.api.telemetry import router as telemetry_router

app = FastAPI(title="API Monitoreo Embalses")

app.include_router(telemetry_router)


@app.get("/")
def root():
    return {"status": "ok"}