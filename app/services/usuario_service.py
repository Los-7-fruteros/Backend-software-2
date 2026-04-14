from app.db.supabase_client import supabase
from app.models.usuario_model import UsuarioInput
from app.utils.logger import logger
from fastapi import HTTPException
from typing import Dict, Any, Optional
import uuid

MAX_LIMIT = 200


# ──────────────────────────────────────────
# QUERIES
# ──────────────────────────────────────────

def get_usuario_by_id(usuario_id: uuid.UUID) -> Dict[str, Any]:
    """Obtener usuario por ID. Lanza 404 si no existe."""
    response = supabase.table("usuario") \
        .select("id, rol, email, nombre, num_telefono, created_at") \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return response.data[0]


def get_usuario_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Obtener usuario por email. Retorna None si no existe."""
    response = supabase.table("usuario") \
        .select("id, rol, email, nombre, num_telefono, created_at") \
        .eq("email", email) \
        .execute()

    return response.data[0] if response.data else None


def list_usuarios(limit: int = 50, offset: int = 0) -> list:
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
    Crea usuario en dos pasos:
    1. Supabase Auth maneja el hasheo de la contraseña
    2. Nuestra tabla usuario almacena datos adicionales (rol, nombre, etc.)
    """
    # Verificar email duplicado
    if get_usuario_by_email(data.email):
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    # ✅ Paso 1: Supabase Auth crea el usuario y hashea la contraseña
    try:
        auth_response = supabase.auth.sign_up({
            "email":    data.email,
            "password": data.contrasena
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear usuario en Auth: {str(e)}")

    if not auth_response.user:
        raise HTTPException(status_code=500, detail="Error al registrar usuario en Auth")

    auth_user_id = auth_response.user.id  # UUID asignado por Supabase Auth

    # ✅ Paso 2: Insertar datos adicionales en nuestra tabla usuario
    response = supabase.table("usuario").insert({
        "id":           auth_user_id,   # ← mismo ID que Supabase Auth
        "rol":          data.rol,
        "email":        data.email,
        "nombre":       data.nombre,
        "num_telefono": data.num_telefono
        # hash_contrasena ya no se almacena aquí ✅
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al guardar datos del usuario")

    logger.info(f"✅ Usuario creado | email={data.email}")
    return response.data[0]


def update_usuario(usuario_id: uuid.UUID, data: UsuarioInput) -> Dict[str, Any]:
    """
    Actualiza datos del usuario.
    Si se envía nueva contraseña la actualiza en Supabase Auth.
    """
    get_usuario_by_id(usuario_id)  # lanza 404 si no existe

    # Verificar email duplicado en otro usuario
    existente = get_usuario_by_email(data.email)
    if existente and existente["id"] != str(usuario_id):
        raise HTTPException(status_code=409, detail="El email ya está en uso")

    # ✅ Actualizar contraseña en Supabase Auth si se envió una nueva
    if data.contrasena:
        try:
            supabase.auth.admin.update_user_by_id(
                str(usuario_id),
                {"password": data.contrasena}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al actualizar contraseña: {str(e)}")

    # Actualizar datos adicionales en nuestra tabla
    response = supabase.table("usuario") \
        .update({
            "rol":          data.rol,
            "email":        data.email,
            "nombre":       data.nombre,
            "num_telefono": data.num_telefono
        }) \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar usuario")

    logger.info(f"✏️ Usuario actualizado | id={usuario_id}")
    return response.data[0]


def delete_usuario(usuario_id: uuid.UUID) -> Dict[str, Any]:
    """
    Elimina usuario de nuestra tabla Y de Supabase Auth.
    """
    get_usuario_by_id(usuario_id)  # lanza 404 si no existe

    # ✅ Eliminar de Supabase Auth
    try:
        supabase.auth.admin.delete_user(str(usuario_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario en Auth: {str(e)}")

    # Eliminar de nuestra tabla
    response = supabase.table("usuario") \
        .delete() \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al eliminar usuario")

    logger.info(f"🗑️ Usuario eliminado | id={usuario_id}")
    return {"message": f"Usuario {usuario_id} eliminado correctamente"}


def set_usuario_rol(usuario_id: uuid.UUID, new_role: str, admin_id: Optional[str] = None) -> Dict[str, Any]:
    """Actualizar únicamente el rol de un usuario existente y registrar auditoría.

    Args:
        usuario_id: UUID del usuario a modificar.
        new_role: nuevo rol a asignar.
        admin_id: id del admin que realiza el cambio (opcional).
    """
    # Obtener usuario existente (lanza 404 si no existe)
    usuario = get_usuario_by_id(usuario_id)
    old_role = usuario.get("rol")

    # Actualizar rol en la tabla usuario
    response = supabase.table("usuario") \
        .update({"rol": new_role}) \
        .eq("id", str(usuario_id)) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar rol del usuario")

    # Intentar registrar auditoría — no bloqueante si falla
    try:
        supabase.table("usuario_rol_audit").insert({
            "usuario_id": str(usuario_id),
            "admin_id": admin_id,
            "old_rol": old_role,
            "new_rol": new_role,
        }).execute()
    except Exception as e:
        logger.warning(f"No se pudo registrar auditoría de rol: {e}")

    logger.info(f"🔁 Rol actualizado | id={usuario_id} -> rol={new_role} (por admin={admin_id})")
    return response.data[0]