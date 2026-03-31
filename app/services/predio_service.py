from app.db.supabase_client import supabase
from app.models.predio_model import PredioInput
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_predio_by_id(predio_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener predio por ID. Lanza 404 si no existe."""
    response = supabase.table("predio") \
        .select("*") \
        .eq("id", str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Predio no encontrado")

    return response.data[0]


def list_predios(
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar todos los predios."""
    limit = min(limit, MAX_LIMIT)

    response = supabase.table("predio") \
        .select("*") \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


def list_predios_by_usuario(
    usuario_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0
) -> list:
    """
    Listar predios asociados a un usuario.
    Resuelve la relación N:M a través de usuario_predio.
    """
    limit = min(limit, MAX_LIMIT)

    # Obtener predio_ids del usuario desde tabla intermedia
    up_response = supabase.table("usuario_predio") \
        .select("predio_id") \
        .eq("usuario_id", str(usuario_id)) \
        .execute()

    if not up_response.data:
        return []

    predio_ids = [r["predio_id"] for r in up_response.data]

    response = supabase.table("predio") \
        .select("*") \
        .in_("id", predio_ids) \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_predio(data: PredioInput) -> Dict[str, Any]:
    """Crear nuevo predio."""
    response = supabase.table("predio").insert({
        "nombre":       data.nombre,
        "ubicacion":    data.ubicacion,
        "tipo_cultivo": data.tipo_cultivo
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear predio")

    logger.info(f"✅ Predio creado | nombre={data.nombre}")
    return response.data[0]


def update_predio(predio_id: uuid.UUID, data: PredioInput) -> Dict[str, Any]:
    """Actualizar predio. Lanza 404 si no existe."""
    get_predio_by_id(predio_id)  # lanza 404 si no existe

    response = supabase.table("predio") \
        .update({
            "nombre":       data.nombre,
            "ubicacion":    data.ubicacion,
            "tipo_cultivo": data.tipo_cultivo
        }) \
        .eq("id", str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar predio")

    logger.info(f"✏️ Predio actualizado | id={predio_id}")
    return response.data[0]


def delete_predio(predio_id: uuid.UUID) -> Dict[str, Any]:
    """
    Eliminar predio por ID. Lanza 404 si no existe.
    Sensores, telemetría y alertas se eliminan en cascada.
    """
    get_predio_by_id(predio_id)  # lanza 404 si no existe

    response = supabase.table("predio") \
        .delete() \
        .eq("id", str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar predio")

    logger.info(f"🗑️ Predio eliminado | id={predio_id}")
    return {"message": f"Predio {predio_id} eliminado correctamente"}


def assign_usuario_predio(usuario_id: uuid.UUID, predio_id: uuid.UUID) -> Dict[str, Any]:
    """
    Asignar usuario a un predio (tabla N:M usuario_predio).
    Lanza 409 si la relación ya existe.
    """
    # Verificar que el predio existe
    get_predio_by_id(predio_id)

    # Verificar que la relación no existe ya
    existing = supabase.table("usuario_predio") \
        .select("*") \
        .eq("usuario_id", str(usuario_id)) \
        .eq("predio_id", str(predio_id)) \
        .execute()

    if existing.data:
        raise HTTPException(
            status_code=409,
            detail="El usuario ya tiene acceso a este predio"
        )

    response = supabase.table("usuario_predio").insert({
        "usuario_id": str(usuario_id),
        "predio_id":  str(predio_id)
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al asignar usuario al predio")

    logger.info(f"🔗 Usuario {usuario_id} asignado a predio {predio_id}")
    return response.data[0]


def remove_usuario_predio(usuario_id: uuid.UUID, predio_id: uuid.UUID) -> Dict[str, Any]:
    """Remover acceso de un usuario a un predio."""
    response = supabase.table("usuario_predio") \
        .delete() \
        .eq("usuario_id", str(usuario_id)) \
        .eq("predio_id",  str(predio_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Relación usuario-predio no encontrada")

    logger.info(f"🔗 Usuario {usuario_id} removido de predio {predio_id}")
    return {"message": f"Usuario {usuario_id} removido del predio {predio_id}"}