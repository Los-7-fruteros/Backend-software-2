from app.db.supabase_client import supabase
from app.models.sensores_model import SensorInput
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional, List
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_sensor_by_id(sensor_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener módulo de sensor por ID. Lanza 404 si no existe."""
    response = supabase.table("sensores") \
        .select("*") \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Módulo de sensor no encontrado")

    return response.data[0]


def get_sensor_by_device_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Obtener módulo de sensor por device_id. Retorna None si no existe."""
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
    """Listar módulos de sensor con filtro opcional por predio."""
    limit = min(limit, MAX_LIMIT)

    query = supabase.table("sensores").select("*")

    if predio_id:
        query = query.eq("predio_id", str(predio_id))

    response = query \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


def count_modulos_por_predio(predio_id: uuid.UUID) -> int:
    """Contar cuántos módulos de sensor tiene un predio."""
    response = supabase.table("sensores") \
        .select("id", count="exact") \
        .eq("predio_id", str(predio_id)) \
        .execute()

    return response.count or 0


def get_all_modulos_predio(predio_id: uuid.UUID) -> List[Dict[str, Any]]:
    """Obtener todos los módulos de sensor de un predio."""
    response = supabase.table("sensores") \
        .select("*") \
        .eq("predio_id", str(predio_id)) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_sensor(data: SensorInput) -> Dict[str, Any]:
    """
    Crear un nuevo módulo de sensor validando:
    - Que el predio existe
    - Que no haya duplicación de device_id
    - Que el nombre sea único dentro del predio (opcional pero recomendado)
    """
    # Validar que el predio existe
    predio = supabase.table("predio") \
        .select("id") \
        .eq("id", str(data.predio_id)) \
        .execute()

    if not predio.data:
        raise HTTPException(status_code=404, detail=f"Predio {data.predio_id} no encontrado")

    # Validar device_id duplicado si se proporciona
    if data.device_id:
        existente = get_sensor_by_device_id(data.device_id)
        if existente:
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un módulo de sensor con device_id '{data.device_id}'. Los device_id deben ser únicos en el sistema."
            )

    # Insertar el nuevo módulo de sensor
    response = supabase.table("sensores").insert({
        "nombre":      data.nombre,
        "nombre_zona": data.nombre_zona,
        "device_id":   data.device_id,
        "predio_id":   str(data.predio_id)
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear módulo de sensor")

    logger.info(
        f"✅ Módulo de sensor creado | nombre={data.nombre} | device_id={data.device_id} | predio={data.predio_id}"
    )
    return response.data[0]


def update_sensor(sensor_id: uuid.UUID, data: SensorInput) -> Dict[str, Any]:
    """
    Actualizar un módulo de sensor.
    Permite actualizar: nombre, nombre_zona, device_id y predio_id.
    Lanza 404 si no existe.
    """
    get_sensor_by_id(sensor_id)  # lanza 404 si no existe

    # Validar device_id duplicado si se está cambiando
    if data.device_id:
        existente = get_sensor_by_device_id(data.device_id)
        if existente and existente["id"] != str(sensor_id):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un módulo de sensor con device_id '{data.device_id}'. Los device_id deben ser únicos en el sistema."
            )

    response = supabase.table("sensores") \
        .update({
            "nombre":      data.nombre,
            "nombre_zona": data.nombre_zona,
            "device_id":   data.device_id,
            "predio_id":   str(data.predio_id)
        }) \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar módulo de sensor")

    logger.info(f"✏️ Módulo de sensor actualizado | id={sensor_id} | nombre={data.nombre}")
    return response.data[0]


def delete_sensor(sensor_id: uuid.UUID) -> Dict[str, Any]:
    """
    Eliminar un módulo de sensor por ID.
    Lanza 404 si no existe.
    Los datos de telemetría se eliminan en cascada (ON DELETE CASCADE en schema).
    """
    sensor = get_sensor_by_id(sensor_id)  # lanza 404 si no existe

    response = supabase.table("sensores") \
        .delete() \
        .eq("id", str(sensor_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar módulo de sensor")

    logger.info(f"🗑️ Módulo de sensor eliminado | id={sensor_id} | nombre={sensor.get('nombre', 'sin nombre')}")
    return {"message": f"Módulo de sensor {sensor_id} eliminado correctamente"}