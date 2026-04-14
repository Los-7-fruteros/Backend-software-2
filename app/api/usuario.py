from fastapi import APIRouter, HTTPException, Query, Path, Depends
from fastapi.security import HTTPBearer
from app.models.usuario_model import UsuarioInput, UsuarioOutput
from app.services.usuario_service import (
    get_usuario_by_id,
    list_usuarios,
    create_usuario,
    update_usuario,
    delete_usuario,
    set_usuario_rol,
    MAX_LIMIT
)
from app.services.auth_service import login
from app.utils.auth_dependency import get_current_user, require_rol
from pydantic import BaseModel
from typing import Dict, Any
import uuid

# ✅ auth_router sin protección — login y registro son públicos
auth_router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ✅ usuarios_router protegido
router = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(get_current_user)]
)


# ──────────────────────────────────────────
# AUTH (público)
# ──────────────────────────────────────────

class LoginInput(BaseModel):
    email: str
    contrasena: str


@auth_router.post("/login")
def login_endpoint(data: LoginInput):
    """🔐 Login — retorna JWT"""
    try:
        return login(data.email, data.contrasena)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")


@auth_router.post("/registro", response_model=UsuarioOutput, status_code=201)
def registro_endpoint(data: UsuarioInput):
    """📝 Registro de nuevo usuario — fuerza rol 'operador' por seguridad."""
    try:
        # Ignorar cualquier rol enviado por el cliente y forzar 'operador'
        data.rol = "operador"
        return create_usuario(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en registro: {str(e)}")


# ──────────────────────────────────────────
# USUARIOS (protegidos)
# ──────────────────────────────────────────

@router.get("/me", response_model=UsuarioOutput)
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """👤 Obtener perfil del usuario autenticado"""
    try:
        return get_usuario_by_id(uuid.UUID(current_user["sub"]))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {str(e)}")


@router.get("", response_model=list[UsuarioOutput])
def get_all_usuarios(
    limit:  int = Query(50, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    _: Dict[str, Any] = Depends(require_rol("admin"))  # ← solo admins
):
    """📋 Listar usuarios — solo admin"""
    try:
        return list_usuarios(limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {str(e)}")


@router.get("/{usuario_id}", response_model=UsuarioOutput)
def get_usuario_endpoint(
    usuario_id:   uuid.UUID       = Path(..., description="ID del usuario"),
    current_user: Dict[str, Any]  = Depends(get_current_user)
):
    """🔍 Obtener usuario por ID"""
    try:
        # Sólo admins o el propio usuario pueden leer este recurso
        if current_user.get("rol") != "admin" and str(usuario_id) != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Acceso denegado.")

        return get_usuario_by_id(usuario_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")


@router.put("/{usuario_id}", response_model=UsuarioOutput)
def update_usuario_endpoint(
    data:         UsuarioInput,
    usuario_id:   uuid.UUID      = Path(..., description="ID del usuario"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """✏️ Actualizar usuario"""
    try:
        # Sólo admins o el propio usuario pueden actualizar
        if current_user.get("rol") != "admin" and str(usuario_id) != current_user.get("sub"):
            raise HTTPException(status_code=403, detail="Acceso denegado.")

        # Si no es admin, no permitir cambiar el rol (se mantiene el rol actual)
        if current_user.get("rol") != "admin":
            data.rol = current_user.get("rol")

        return update_usuario(usuario_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")


class RoleUpdate(BaseModel):
    rol: str


@router.patch("/{usuario_id}/rol", response_model=UsuarioOutput)
def update_usuario_rol(
    usuario_id: uuid.UUID = Path(..., description="ID del usuario"),
    payload: RoleUpdate = None,
    admin_user: Dict[str, Any] = Depends(require_rol("admin"))  # sólo admin puede cambiar roles
):
    """🔧 Endpoint para que un admin cambie el rol de un usuario. Registra auditoría."""
    try:
        admin_id = admin_user.get("sub")
        return set_usuario_rol(usuario_id, payload.rol, admin_id=admin_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar rol: {str(e)}")


@router.delete("/{usuario_id}")
def delete_usuario_endpoint(
    usuario_id: uuid.UUID      = Path(..., description="ID del usuario"),
    _:          Dict[str, Any] = Depends(require_rol("admin"))  # ← solo admins
):
    """🗑️ Eliminar usuario — solo admin"""
    try:
        return delete_usuario(usuario_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")