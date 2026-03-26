from app.db.supabase_client import supabase


def get_sensor_by_deveui(deveui: str):
    response = supabase.table("sensores") \
        .select("*") \
        .eq("deveui", deveui) \
        .execute()

    return response.data


def create_sensor(deveui: str):
    """
    Solo para testing en Sprint 1.
    En producción esto debería ser manual (H7).
    """
    response = supabase.table("sensores").insert({
        "deveui": deveui,
        "sector": "default",
        "predio_id": 1  # ⚠️ usar predio ficticio
    }).execute()

    return response.data[0]


def insert_telemetry(data):
    # 1. Buscar sensor
    sensor = get_sensor_by_deveui(data.deveui)

    if not sensor:
        sensor = create_sensor(data.deveui)
    else:
        sensor = sensor[0]

    sensor_id = sensor["id"]

    # 2. Insertar telemetría
    response = supabase.table("telemetria").insert({
        "sensor_id": sensor_id,
        "humedad": data.humedad,
        "temperatura": data.temperatura,
        "ph": data.ph,
        "voltaje": data.voltaje
    }).execute()

    return {
        "message": "Telemetría insertada correctamente",
        "sensor_id": sensor_id,
        "data": response.data
    }