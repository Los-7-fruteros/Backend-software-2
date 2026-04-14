from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.utils.auth_dependency import get_current_user
from app.models.telemetry import TelemetryInput
from app.services.telemetry_service import insert_telemetry

router = APIRouter(
    prefix="/api/telemetry",
    tags=["Telemetría"],
    dependencies=[Depends(get_current_user)]  # ← protege todo el router
)


@router.post("/telemetry")
def receive_telemetry(data: TelemetryInput):
    try:
        return insert_telemetry(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))