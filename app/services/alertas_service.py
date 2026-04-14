from app.db.supabase_client import supabase
from app.models.alertas_model import AlertaInput
from app.services.sensores_service import get_sensor_by_id
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_alerta_by_id(alerta_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener alerta por ID. Lanza 404 si no existe."""
    response = supabase.table("alertas") \
        .select("*") \
        .eq("id", str(alerta_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    return response.data[0]


def list_alertas(
    sensor_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar alertas con filtros opcionales."""
    limit = min(limit, MAX_LIMIT)

    query = supabase.table("alertas").select("*")

    if sensor_id:
        query = query.eq("sensor_id", str(sensor_id))

    response = query \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


def list_alertas_by_predio(
    predio_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar alertas de todos los sensores de un predio."""
    limit = min(limit, MAX_LIMIT)

    # Obtener sensor_ids del predio
    sensores_response = supabase.table("sensores") \
        .select("id") \
        .eq("predio_id", str(predio_id)) \
        .execute()

    if not sensores_response.data:
        return []

    sensor_ids = [s["id"] for s in sensores_response.data]

    response = supabase.table("alertas") \
        .select("*") \
        .in_("sensor_id", sensor_ids) \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_alerta(data: AlertaInput) -> Dict[str, Any]:
    """Crear alerta validando que el sensor existe."""
    sensor = get_sensor_by_id(data.sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor {data.sensor_id} no encontrado")

    response = supabase.table("alertas").insert({
        "sensor_id": str(data.sensor_id),
        "tipo":      data.tipo,
        "valor":     data.valor,
        "mensaje":   data.mensaje
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear alerta")

    logger.info(f"✅ Alerta creada | sensor={data.sensor_id} | tipo={data.tipo}")
    return response.data[0]


def delete_alerta(alerta_id: uuid.UUID) -> Dict[str, Any]:
    """Eliminar alerta por ID. Lanza 404 si no existe."""
    get_alerta_by_id(alerta_id)  # lanza 404 si no existe

    response = supabase.table("alertas") \
        .delete() \
        .eq("id", str(alerta_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar alerta")

    logger.info(f"🗑️ Alerta eliminada | id={alerta_id}")
    return {"message": f"Alerta {alerta_id} eliminada correctamente"}