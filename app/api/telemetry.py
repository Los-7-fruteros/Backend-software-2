from fastapi import APIRouter, HTTPException
from app.models.telemetry import TelemetryInput
from app.services.telemetry_service import insert_telemetry

router = APIRouter(prefix="/api", tags=["Telemetry"])


@router.post("/telemetry")
def receive_telemetry(data: TelemetryInput):
    try:
        return insert_telemetry(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))