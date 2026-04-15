from fastapi import APIRouter, HTTPException, Query, Path, Depends
from fastapi.security import HTTPBearer
from app.models.usuario_model import UsuarioInput, UsuarioOutput
from app.services.usuario_service import (
    get_usuario_by_id,
    list_usuarios,
    create_usuario,
    update_usuario,
    delete_usuario,
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


@auth_router.get("/health")
def auth_health():
    """Test endpoint"""
    return {"status": "ok", "auth_service": "running"}


@auth_router.post("/login")
def login_endpoint(data: LoginInput):
    """🔐 Login — retorna JWT"""
    print(f"DEBUG: Login attempt for {data.email}")
    try:
        result = login(data.email, data.contrasena)
        print(f"DEBUG: Login success for {data.email}")
        return result
    except HTTPException as e:
        print(f"DEBUG: HTTP exception: {e.detail}")
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")


@auth_router.post("/registro", response_model=UsuarioOutput, status_code=201)
def registro_endpoint(data: UsuarioInput):
    """📝 Registro de nuevo usuario"""
    try:
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
        return update_usuario(usuario_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar usuario: {str(e)}")


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
