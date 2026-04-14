from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.utils.auth_dependency import get_current_user
from typing import Optional
from app.models.sensores_model import SensorInput, SensorOutput
from app.services.sensores_service import (
    get_sensor_by_id,
    list_sensores,
    create_sensor,
    update_sensor,
    delete_sensor,
    count_modulos_por_predio,
    get_all_modulos_predio,
    MAX_LIMIT
)
import uuid

router = APIRouter(
    prefix="/api/sensores",
    tags=["Sensores (Módulos)"],
    dependencies=[Depends(get_current_user)]  # ← protege todo el router
)


# ── Rutas estáticas primero ──────────────────────────

@router.get(
    "/predio/{predio_id}",
    response_model=list[SensorOutput],
    summary="Listar todos los módulos de sensor de un predio",
    description="Obtiene todos los módulos de sensor (zonas de cultivo) configurados para un predio específico. "
                "Cada módulo monitorea independientemente su zona de cultivo."
)
def get_sensores_by_predio(
    predio_id: uuid.UUID = Path(..., description="ID del predio"),
    limit:     int       = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int       = Query(0, ge=0)
):
    """
    📍 Listar todos los módulos de sensor de un predio
    
    Retorna una lista de todos los módulos configurados para monitorear diferentes
    zonas de cultivo dentro del predio especificado.
    """
    try:
        return list_sensores(predio_id=predio_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener módulos de sensor del predio: {str(e)}")


@router.get(
    "/predio/{predio_id}/count",
    summary="Contar módulos de sensor en un predio",
    description="Devuelve la cantidad total de módulos de sensor configurados en un predio."
)
def count_sensores_predio(
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """
    📊 Contar módulos de sensor en un predio
    
    Útil para validar si un predio tiene múltiples módulos configurados.
    """
    try:
        count = count_modulos_por_predio(predio_id)
        return {"predio_id": str(predio_id), "total_modulos": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contar módulos: {str(e)}")


# ── Rutas dinámicas después ──────────────────────────

@router.get(
    "",
    response_model=list[SensorOutput],
    summary="Listar todos los módulos de sensor",
    description="Obtiene todos los módulos de sensor del sistema, opcionalmente filtrados por predio."
)
def get_all_sensores(
    predio_id: Optional[uuid.UUID] = Query(None, description="Filtrar por predio (opcional)"),
    limit:     int                  = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int                  = Query(0, ge=0)
):
    """📋 Listar todos los módulos de sensor"""
    try:
        return list_sensores(predio_id=predio_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar módulos de sensor: {str(e)}")


@router.post(
    "",
    response_model=SensorOutput,
    status_code=201,
    summary="Crear nuevo módulo de sensor",
    description="Agrega un nuevo módulo de sensor a un predio. "
                "Cada módulo puede monitorear una zona de cultivo distinta dentro del mismo predio."
)
def create_sensor_endpoint(data: SensorInput):
    """
    ➕ Crear nuevo módulo de sensor
    
    Permite agregar un módulo de sensor a un predio para monitorear una zona de cultivo específica.
    Soporta múltiples módulos por predio.
    
    **Parámetros:**
    - `nombre`: Identificador descriptivo del módulo (ej: "Sensor Zona Norte")
    - `nombre_zona`: Descripción de la zona a monitorear (ej: "Campo de tomates")
    - `device_id`: ID único del dispositivo (debe ser único en todo el sistema)
    - `predio_id`: ID del predio al que pertenece este módulo
    """
    try:
        return create_sensor(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear módulo de sensor: {str(e)}")


@router.get(
    "/{sensor_id}",
    response_model=SensorOutput,
    summary="Obtener módulo de sensor por ID",
    description="Recupera la información de un módulo de sensor específico."
)
def get_sensor_endpoint(
    sensor_id: uuid.UUID = Path(..., description="ID del módulo de sensor")
):
    """🔍 Obtener módulo de sensor por ID"""
    try:
        return get_sensor_by_id(sensor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener módulo de sensor: {str(e)}")


@router.put(
    "/{sensor_id}",
    response_model=SensorOutput,
    summary="Actualizar módulo de sensor",
    description="Modifica los parámetros de un módulo de sensor existente (nombre, zona, device_id, etc)."
)
def update_sensor_endpoint(
    data:      SensorInput,
    sensor_id: uuid.UUID = Path(..., description="ID del módulo de sensor")
):
    """
    ✏️ Actualizar módulo de sensor
    
    Permite cambiar los parámetros de configuración de un módulo.
    """
    try:
        return update_sensor(sensor_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar módulo de sensor: {str(e)}")


@router.delete(
    "/{sensor_id}",
    summary="Eliminar módulo de sensor",
    description="Elimina un módulo de sensor y todos sus datos de telemetría asociados."
)
def delete_sensor_endpoint(
    sensor_id: uuid.UUID = Path(..., description="ID del módulo de sensor")
):
    """
    🗑️ Eliminar módulo de sensor
    
    Elimina completamente un módulo de sensor del predio.
    También elimina en cascada toda la telemetría asociada a este módulo.
    """
    try:
        return delete_sensor(sensor_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar módulo de sensor: {str(e)}")