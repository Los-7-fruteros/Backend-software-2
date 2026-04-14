from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.utils.auth_dependency import get_current_user
from app.models.telemetria_model import TelemetriaInput, TelemetriaOutput
from app.services.telemetria_service import (
    insert_telemetry_data,
    get_telemetry_by_id,
    list_telemetry,
    MAX_LIMIT
)
import uuid

router = APIRouter(
    prefix="/api/telemetry",
    tags=["Telemetría"],
    dependencies=[Depends(get_current_user)]  # ← protege todo el router
)


@router.post(
    "/",
    response_model=TelemetriaOutput,
    status_code=201,
    summary="Registrar datos de telemetría",
    description="Recibe y almacena datos de telemetría de un módulo de sensor. "
                "Soporta identificación por sensor_id (UUID) o device_id (string)."
)
def receive_telemetry(data: TelemetriaInput):
    """
    ➕ Registrar datos de telemetría
    
    Recibe mediciones de un módulo de sensor para una zona de cultivo.
    
    **Identificación del módulo (use una):**
    - `sensor_id`: UUID del módulo de sensor (preferido si ya lo conoce)
    - `device_id`: ID del dispositivo físico (alternativo, busca el sensor por este identificador)
    
    **Ejemplo con sensor_id:**
    ```json
    {
        "sensor_id": "550e8400-e29b-41d4-a716-446655440000",
        "temperatura": 25.5,
        "humedad": 65.0,
        "ph": 6.5,
        "voltaje": 12.0
    }
    ```
    
    **Ejemplo con device_id:**
    ```json
    {
        "device_id": "device_001",
        "temperatura": 25.5,
        "humedad": 65.0
    }
    ```
    """
    try:
        return insert_telemetry_data(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar telemetría: {str(e)}")


@router.get(
    "/{telemetry_id}",
    response_model=TelemetriaOutput,
    summary="Obtener registro de telemetría",
    description="Recupera un registro específico de telemetría por su ID."
)
def get_telemetry_endpoint(
    telemetry_id: uuid.UUID = Path(..., description="ID del registro de telemetría")
):
    """🔍 Obtener registro de telemetría por ID"""
    try:
        return get_telemetry_by_id(telemetry_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener telemetría: {str(e)}")


@router.get(
    "",
    response_model=list[TelemetriaOutput],
    summary="Listar telemetría de un módulo",
    description="Obtiene registros de telemetría de un módulo de sensor específico."
)
def list_telemetry_endpoint(
    sensor_id: uuid.UUID = Query(..., description="ID del módulo de sensor"),
    limit:     int       = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int       = Query(0, ge=0)
):
    """
    📊 Listar telemetría de un módulo de sensor
    
    Retorna todos los registros de telemetría para un módulo específico,
    permitiendo ver el histórico de mediciones.
    """
    try:
        return list_telemetry(sensor_id=sensor_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar telemetría: {str(e)}")