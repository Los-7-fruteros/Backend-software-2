from app.db.supabase_client import supabase
from app.models.telemetria_model import TelemetriaInput
from app.services.umbrales_service import check_umbrales
from app.services.sensores_service import get_sensor_by_id, get_sensor_by_device_id as get_sensor_by_device_id_service
from app.utils.logger import logger
from typing import Dict, Any, Optional
from fastapi import HTTPException
import uuid

MAX_LIMIT = 200  # techo de paginación


# ──────────────────────────────────────────
# IDENTIFICACIÓN DE SENSORES
# ──────────────────────────────────────────

def resolve_sensor_id(sensor_id: Optional[uuid.UUID] = None, device_id: Optional[str] = None) -> uuid.UUID:
    """
    Resuelve el ID del sensor a partir de sensor_id o device_id.
    
    Prioridad:
    1. Si viene sensor_id (UUID), usarlo directamente
    2. Si viene device_id (string), buscar el sensor por device_id
    3. Si ninguno, lanzar error
    
    Retorna: UUID del sensor
    Lanza HTTPException si no puede resolver
    """
    if sensor_id:
        # Validar que el sensor existe
        try:
            get_sensor_by_id(sensor_id)
            return sensor_id
        except HTTPException:
            raise HTTPException(
                status_code=404,
                detail=f"Módulo de sensor con ID {sensor_id} no encontrado"
            )
    
    elif device_id:
        # Buscar sensor por device_id
        sensor = get_sensor_by_device_id_service(device_id)
        if not sensor:
            raise HTTPException(
                status_code=404,
                detail=f"Módulo de sensor con device_id '{device_id}' no encontrado. "
                       f"Verifique que el dispositivo está registrado en el sistema."
            )
        return uuid.UUID(sensor["id"])
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar identificación del módulo de sensor usando 'sensor_id' (UUID) o 'device_id' (string)"
        )


def get_sensor_details(sensor_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener detalles completos de un módulo de sensor."""
    return get_sensor_by_id(sensor_id)


# ──────────────────────────────────────────
# TELEMETRÍA
# ──────────────────────────────────────────

def insert_telemetry_data(data: TelemetriaInput) -> Dict[str, Any]:
    """
    Insertar datos de telemetría.
    
    Soporta identificación del módulo de sensor por:
    - sensor_id: UUID del módulo (preferido, más directo)
    - device_id: String del ID del dispositivo (alternativo)
    
    El sistema resuelve automáticamente cuál de los dos usar.
    """
    # Resolver el sensor_id a partir de los datos proporcionados
    resolved_sensor_id = resolve_sensor_id(sensor_id=data.sensor_id, device_id=data.device_id)
    
    # Obtener información del sensor
    sensor = get_sensor_details(resolved_sensor_id)
    
    # Insertar telemetría con los datos validados
    response = supabase.table("telemetria").insert({
        "sensor_id":    str(resolved_sensor_id),
        "humedad":      data.humedad,
        "temperatura":  data.temperatura,
        "ph":           data.ph,
        "voltaje":      data.voltaje
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al insertar datos de telemetría")

    # ✅ Disparar verificación de umbrales después de insertar
    try:
        check_umbrales(sensor, data)
    except Exception as e:
        logger.warning(f"⚠️ Error al verificar umbrales: {str(e)}")

    logger.info(
        f"✅ Telemetría registrada | módulo={sensor.get('nombre', 'sin nombre')} | sensor_id={resolved_sensor_id}"
    )
    
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
    """Listar telemetría de un módulo de sensor con filtros opcionales y límite máximo."""
    limit = min(limit, MAX_LIMIT)  # ← evita queries abusivos

    query = supabase.table("telemetria").select("*")

    if sensor_id:
        query = query.eq("sensor_id", str(sensor_id))

    response = query \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []