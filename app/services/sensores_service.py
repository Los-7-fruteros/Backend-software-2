from app.db.supabase_client import supabase
from app.models.sensores_model import SensorInput
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_sensor_by_id(sensor_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener sensor por ID. Lanza 404 si no existe."""
    response = supabase.table("sensores") \
        .select("*") \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    return response.data[0]


def get_sensor_by_device_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Obtener sensor por device_id. Retorna None si no existe."""
    response = supabase.table("sensores") \
        .select("*") \
        .eq("device_id", device_id) \
        .execute()

    return response.data[0] if response.data else None


def list_sensores(
    predio_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar sensores con filtro opcional por predio."""
    limit = min(limit, MAX_LIMIT)

    query = supabase.table("sensores").select("*")

    if predio_id:
        query = query.eq("predio_id", str(predio_id))

    response = query \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_sensor(data: SensorInput) -> Dict[str, Any]:
    """
    Crear sensor validando que el predio existe
    y que no haya un sensor duplicado con el mismo device_id.
    """
    # Validar que el predio existe
    predio = supabase.table("predio") \
        .select("id") \
        .eq("id", str(data.predio_id)) \
        .execute()

    if not predio.data:
        raise HTTPException(status_code=404, detail=f"Predio {data.predio_id} no encontrado")

    # Validar device_id duplicado
    if data.device_id:
        existente = get_sensor_by_device_id(data.device_id)
        if existente:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un sensor con device_id '{data.device_id}'"
            )

    response = supabase.table("sensores").insert({
        "sector":    data.sector,
        "device_id": data.device_id,
        "predio_id": str(data.predio_id)
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear sensor")

    logger.info(f"✅ Sensor creado | device_id={data.device_id} | predio={data.predio_id}")
    return response.data[0]


def update_sensor(sensor_id: uuid.UUID, data: SensorInput) -> Dict[str, Any]:
    """
    Actualizar sector y/o device_id de un sensor.
    Lanza 404 si no existe.
    """
    get_sensor_by_id(sensor_id)  # lanza 404 si no existe

    # Validar device_id duplicado si se está cambiando
    if data.device_id:
        existente = get_sensor_by_device_id(data.device_id)
        if existente and existente["id"] != str(sensor_id):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un sensor con device_id '{data.device_id}'"
            )

    response = supabase.table("sensores") \
        .update({
            "sector":    data.sector,
            "device_id": data.device_id,
            "predio_id": str(data.predio_id)
        }) \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar sensor")

    logger.info(f"✏️ Sensor actualizado | id={sensor_id}")
    return response.data[0]


def delete_sensor(sensor_id: uuid.UUID) -> Dict[str, Any]:
    """
    Eliminar sensor por ID.
    Lanza 404 si no existe.
    Las alertas y telemetría se eliminan en cascada (ON DELETE CASCADE en schema).
    """
    get_sensor_by_id(sensor_id)  # lanza 404 si no existe

    response = supabase.table("sensores") \
        .delete() \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar sensor")

    logger.info(f"🗑️ Sensor eliminado | id={sensor_id}")
    return {"message": f"Sensor {sensor_id} eliminado correctamente"}