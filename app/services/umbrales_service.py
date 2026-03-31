from app.db.supabase_client import supabase
from app.models.umbrales_model import UmbralInput
from app.models.telemetria_model import TelemetriaInput
from app.services.alertas_service import create_alerta  # ← fuente única
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_umbrales_by_predio(predio_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """Obtener umbrales configurados para un predio."""
    response = supabase.table("umbrales") \
        .select("*") \
        .eq("predio_id", str(predio_id)) \
        .execute()

    return response.data[0] if response.data else None


def get_umbral_by_id(umbral_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener umbral por ID. Lanza 404 si no existe."""
    response = supabase.table("umbrales") \
        .select("*") \
        .eq("id", str(umbral_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Umbral no encontrado")

    return response.data[0]


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_umbral(data: UmbralInput) -> Dict[str, Any]:
    """
    Crear umbral para un predio.
    Lanza 409 si el predio ya tiene umbrales configurados.
    """
    existente = get_umbrales_by_predio(data.predio_id)
    if existente:
        raise HTTPException(
            status_code=409,
            detail=f"El predio {data.predio_id} ya tiene umbrales configurados, usa PUT para actualizar"
        )

    response = supabase.table("umbrales").insert({
        "humedad_min":     data.humedad_min,
        "humedad_max":     data.humedad_max,
        "temperatura_min": data.temperatura_min,
        "temperatura_max": data.temperatura_max,
        "ph_min":          data.ph_min,
        "ph_max":          data.ph_max,
        "voltaje_min":     data.voltaje_min,
        "predio_id":       str(data.predio_id)
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear umbral")

    logger.info(f"✅ Umbral creado | predio={data.predio_id}")
    return response.data[0]


def update_umbral(predio_id: uuid.UUID, data: UmbralInput) -> Dict[str, Any]:
    """
    Actualizar umbrales de un predio.
    Lanza 404 si no existen umbrales para ese predio.
    """
    existente = get_umbrales_by_predio(predio_id)
    if not existente:
        raise HTTPException(
            status_code=404,
            detail=f"No hay umbrales configurados para el predio {predio_id}"
        )

    response = supabase.table("umbrales") \
        .update({
            "humedad_min":     data.humedad_min,
            "humedad_max":     data.humedad_max,
            "temperatura_min": data.temperatura_min,
            "temperatura_max": data.temperatura_max,
            "ph_min":          data.ph_min,
            "ph_max":          data.ph_max,
            "voltaje_min":     data.voltaje_min,
        }) \
        .eq("predio_id", str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar umbral")

    logger.info(f"✏️ Umbral actualizado | predio={predio_id}")
    return response.data[0]


def delete_umbral(predio_id: uuid.UUID) -> Dict[str, Any]:
    """Eliminar umbrales de un predio. Lanza 404 si no existen."""
    existente = get_umbrales_by_predio(predio_id)
    if not existente:
        raise HTTPException(
            status_code=404,
            detail=f"No hay umbrales configurados para el predio {predio_id}"
        )

    response = supabase.table("umbrales") \
        .delete() \
        .eq("predio_id", str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar umbral")

    logger.info(f"🗑️ Umbral eliminado | predio={predio_id}")
    return {"message": f"Umbrales del predio {predio_id} eliminados correctamente"}


# ──────────────────────────────────────────
# CHECK PRINCIPAL (usado por telemetria_service)
# ──────────────────────────────────────────

def check_umbrales(sensor: Dict[str, Any], data: TelemetriaInput) -> list[Dict[str, Any]]:
    """
    Compara los valores de telemetría contra los umbrales del predio.
    Crea una alerta por cada variable que esté fuera de rango.
    Retorna la lista de alertas generadas (puede ser vacía).
    """
    predio_id = sensor.get("predio_id")
    sensor_id = sensor.get("id")

    if not predio_id:
        logger.info(f"Sensor {sensor_id} sin predio asignado, omitiendo check de umbrales")
        return []

    umbrales = get_umbrales_by_predio(uuid.UUID(predio_id))
    if not umbrales:
        logger.info(f"Sin umbrales configurados para predio={predio_id}")
        return []

    alertas_generadas = []

    # voltaje solo tiene min según el schema → max=None
    checks = [
        ("humedad",     data.humedad,     umbrales.get("humedad_min"),     umbrales.get("humedad_max")),
        ("temperatura", data.temperatura, umbrales.get("temperatura_min"), umbrales.get("temperatura_max")),
        ("ph",          data.ph,          umbrales.get("ph_min"),          umbrales.get("ph_max")),
        ("voltaje",     data.voltaje,     umbrales.get("voltaje_min"),     None),
    ]

    for campo, valor, minimo, maximo in checks:
        if valor is None:
            continue

        alerta = _evaluar_campo(sensor_id, campo, valor, minimo, maximo)
        if alerta:
            alertas_generadas.append(alerta)

    return alertas_generadas


# ──────────────────────────────────────────
# HELPERS INTERNOS
# ──────────────────────────────────────────

def _evaluar_campo(
    sensor_id: str,
    campo: str,
    valor: float,
    minimo: Optional[float],
    maximo: Optional[float]
) -> Optional[Dict[str, Any]]:
    """
    Evalúa si un valor está fuera del rango [min, max].
    Retorna la alerta creada o None si está dentro del rango.
    """
    if minimo is not None and valor < minimo:
        return create_alerta(sensor_id=sensor_id, tipo=campo, valor=valor,
            mensaje=f"{campo.capitalize()} por debajo del mínimo: {valor} < {minimo}"
        )

    if maximo is not None and valor > maximo:
        return create_alerta(sensor_id=sensor_id, tipo=campo, valor=valor,
            mensaje=f"{campo.capitalize()} por encima del máximo: {valor} > {maximo}"
        )

    return None