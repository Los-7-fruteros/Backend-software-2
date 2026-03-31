from app.db.supabase_client import supabase
from app.models.usuario_model import UsuarioInput
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import bcrypt
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_usuario_by_id(usuario_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener usuario por ID. Lanza 404 si no existe."""
    response = supabase.table("usuario") \
        .select("*") \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return response.data[0]


def get_usuario_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Obtener usuario por email. Retorna None si no existe."""
    response = supabase.table("usuario") \
        .select("*") \
        .eq("email", email) \
        .execute()

    return response.data[0] if response.data else None


def list_usuarios(
    limit: int = 50,
    offset: int = 0
) -> list:
    """Listar usuarios sin exponer hash_contrasena."""
    limit = min(limit, MAX_LIMIT)

    response = supabase.table("usuario") \
        .select("id, rol, email, nombre, num_telefono, created_at") \
        .range(offset, offset + limit - 1) \
        .order("created_at", desc=True) \
        .execute()

    return response.data if response.data else []


# ──────────────────────────────────────────
# MUTACIONES
# ──────────────────────────────────────────

def create_usuario(data: UsuarioInput) -> Dict[str, Any]:
    """
    Crear usuario hasheando la contraseña.
    Lanza 409 si el email ya existe.
    """
    # Verificar email duplicado
    if get_usuario_by_email(data.email):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # Hashear contraseña
    hash_bytes = bcrypt.hashpw(data.contrasena.encode("utf-8"), bcrypt.gensalt())
    hash_str = hash_bytes.decode("utf-8")

    response = supabase.table("usuario").insert({
        "rol":             data.rol,
        "email":           data.email,
        "hash_contrasena": hash_str,
        "nombre":          data.nombre,
        "num_telefono":    data.num_telefono
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al crear usuario")

    logger.info(f"✅ Usuario creado | email={data.email}")
    return response.data[0]


def update_usuario(usuario_id: uuid.UUID, data: UsuarioInput) -> Dict[str, Any]:
    """
    Actualizar usuario. Lanza 404 si no existe.
    Rehashea la contraseña si se envía una nueva.
    """
    get_usuario_by_id(usuario_id)  # lanza 404 si no existe

    # Verificar email duplicado en otro usuario
    existente = get_usuario_by_email(data.email)
    if existente and existente["id"] != str(usuario_id):
        raise HTTPException(status_code=409, detail="El email ya está en uso")

    hash_bytes = bcrypt.hashpw(data.contrasena.encode("utf-8"), bcrypt.gensalt())
    hash_str = hash_bytes.decode("utf-8")

    response = supabase.table("usuario") \
        .update({
            "rol":             data.rol,
            "email":           data.email,
            "hash_contrasena": hash_str,
            "nombre":          data.nombre,
            "num_telefono":    data.num_telefono
        }) \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")

    logger.info(f"✏️ Usuario actualizado | id={usuario_id}")
    return response.data[0]


def delete_usuario(usuario_id: uuid.UUID) -> Dict[str, Any]:
    """Eliminar usuario. Lanza 404 si no existe."""
    get_usuario_by_id(usuario_id)  # lanza 404 si no existe

    response = supabase.table("usuario") \
        .delete() \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")

    logger.info(f"🗑️ Usuario eliminado | id={usuario_id}")
    return {"message": f"Usuario {usuario_id} eliminado correctamente"}