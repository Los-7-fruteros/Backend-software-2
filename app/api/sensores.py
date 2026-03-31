from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from app.models.sensores_model import SensorInput, SensorOutput
from app.services.sensores_service import (
    get_sensor_by_id,
    list_sensores,
    create_sensor,
    update_sensor,
    delete_sensor,
    MAX_LIMIT
)
import uuid

router = APIRouter(prefix="/api/sensores", tags=["Sensores"])


# ── Rutas estáticas primero ──────────────────────────

@router.get("/predio/{predio_id}", response_model=list[SensorOutput])
def get_sensores_by_predio(
    predio_id: uuid.UUID = Path(..., description="ID del predio"),
    limit:     int       = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int       = Query(0, ge=0)
):
    """📍 Listar todos los sensores de un predio"""
    try:
        return list_sensores(predio_id=predio_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sensores del predio: {str(e)}")


# ── Rutas dinámicas después ──────────────────────────

@router.get("", response_model=list[SensorOutput])
def get_all_sensores(
    predio_id: Optional[uuid.UUID] = Query(None, description="Filtrar por predio"),
    limit:     int                  = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int                  = Query(0, ge=0)
):
    """📋 Listar todos los sensores"""
    try:
        return list_sensores(predio_id=predio_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar sensores: {str(e)}")


@router.post("", response_model=SensorOutput, status_code=201)
def create_sensor_endpoint(data: SensorInput):
    """➕ Crear nuevo sensor"""
    try:
        return create_sensor(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear sensor: {str(e)}")


@router.get("/{sensor_id}", response_model=SensorOutput)
def get_sensor_endpoint(
    sensor_id: uuid.UUID = Path(..., description="ID del sensor")
):
    """🔍 Obtener sensor por ID"""
    try:
        return get_sensor_by_id(sensor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sensor: {str(e)}")


@router.put("/{sensor_id}", response_model=SensorOutput)
def update_sensor_endpoint(
    data:      SensorInput,
    sensor_id: uuid.UUID = Path(..., description="ID del sensor")
):
    """✏️ Actualizar sensor"""
    try:
        return update_sensor(sensor_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar sensor: {str(e)}")


@router.delete("/{sensor_id}")
def delete_sensor_endpoint(
    sensor_id: uuid.UUID = Path(..., description="ID del sensor")
):
    """🗑️ Eliminar sensor"""
    try:
        return delete_sensor(sensor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar sensor: {str(e)}")