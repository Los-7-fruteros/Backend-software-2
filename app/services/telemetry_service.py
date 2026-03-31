from fastapi import HTTPException

from app.db.supabase_client import supabase
from app.models.telemetria_model import TelemetriaInput
from app.services.umbrales_service import check_umbrales


def get_sensor_by_deveui(deveui: str):
    """El frontend envía `deveui`, pero en el schema actual se guarda como `device_id`."""
    response = (
        supabase.table("sensores")
        .select("*")
        .eq("device_id", deveui)
        .execute()
    )

    return response.data[0] if response.data else None


def get_default_predio_id():
    response = supabase.table("predio").select("id").limit(1).execute()
    if response.data:
        return response.data[0]["id"]
    return None


def create_sensor(deveui: str):
    """
    Auto-creación mínima para testing desde telemetría.
    Usa el primer predio disponible si existe.
    """
    payload = {
        "device_id": deveui,
        "sector": "default",
    }

    predio_id = get_default_predio_id()
    if predio_id:
        payload["predio_id"] = predio_id

    response = supabase.table("sensores").insert(payload).execute()

    if not response.data:
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear automáticamente el sensor para la telemetría",
        )

    return response.data[0]


def insert_telemetry(data):
    sensor = get_sensor_by_deveui(data.deveui)

    if not sensor:
        sensor = create_sensor(data.deveui)

    sensor_id = sensor["id"]

    response = supabase.table("telemetria").insert(
        {
            "sensor_id": sensor_id,
            "humedad": data.humedad,
            "temperatura": data.temperatura,
            "ph": data.ph,
            "voltaje": data.voltaje,
        }
    ).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al insertar telemetría")

    try:
        threshold_payload = TelemetriaInput(
            sensor_id=sensor_id,
            humedad=data.humedad,
            temperatura=data.temperatura,
            ph=data.ph,
            voltaje=data.voltaje,
        )
        check_umbrales(sensor, threshold_payload)
    except Exception:
        # Si los umbrales fallan no rompemos la inserción principal de telemetría.
        pass

    return {
        "message": "Telemetría insertada correctamente",
        "sensor_id": sensor_id,
        "data": response.data,
    }