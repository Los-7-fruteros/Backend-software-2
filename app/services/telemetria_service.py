from app.db.supabase_client import supabase
from app.models.telemetria_model import TelemetriaInput
from app.services.umbrales_service import check_umbrales
from app.services.sensores_service import get_sensor_by_id
from typing import Dict, Any, Optional
from fastapi import HTTPException
import uuid

MAX_LIMIT = 200  # techo de paginación


# ──────────────────────────────────────────
# SENSORES
# ──────────────────────────────────────────

def get_sensor_by_device_id(device_id: str) -> Dict[str, Any] | None:
    """Obtener sensor por device_id (antes llamado deveui — no existe en schema)"""
    response = supabase.table("sensores") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()
    return response.data[0] if response.data else None



# ──────────────────────────────────────────
# TELEMETRÍA
# ──────────────────────────────────────────

def insert_telemetry_data(sensor_id: uuid.UUID, data: TelemetriaInput) -> Dict[str, Any]:
    sensor = get_sensor_by_id(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor {sensor_id} no encontrado")

    # Insertar telemetría
    response = supabase.table("telemetria").insert({
        "sensor_id": str(sensor_id),
        "humedad": data.humedad,
        "temperatura": data.temperatura,
        "ph": data.ph,
        "voltaje": data.voltaje
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al insertar telemetría")

    # ✅ Disparar check de umbrales después de insertar
    check_umbrales(sensor, data)

    return response.data[0]


def get_telemetry_by_id(telemetry_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener un registro específico de telemetría. Lanza 404 si no existe."""
    response = supabase.table("telemetria") \
        .select("*") \
        .eq("id", str(telemetry_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Registro de telemetría no encontrado")

    return response.data[0]


def list_telemetry(
    sensor_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar telemetría con filtros opcionales y límite máximo."""
    limit = min(limit, MAX_LIMIT)  # ← evita queries abusivos

    query = supabase.table("telemetria").select("*")

    if sensor_id:
        query = query.eq("sensor_id", str(sensor_id))

    response = query \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []