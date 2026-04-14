from fastapi import APIRouter, HTTPException, Query, Path, Depends
from app.utils.auth_dependency import get_current_user
from app.models.predio_model import PredioInput, PredioOutput
from app.services.predio_service import (
    get_predio_by_id,
    list_predios,
    list_predios_by_usuario,
    create_predio,
    update_predio,
    delete_predio,
    assign_usuario_predio,
    remove_usuario_predio,
    MAX_LIMIT
)
import uuid

router = APIRouter(
    prefix="/api/predios",
    tags=["Predios"],
    dependencies=[Depends(get_current_user)]  # ← protege todo el router
)


# ── Rutas estáticas primero ──────────────────────────

@router.get("/usuario/{usuario_id}", response_model=list[PredioOutput])
def get_predios_by_usuario(
    usuario_id: uuid.UUID = Path(..., description="ID del usuario"),
    limit:      int       = Query(50, ge=1, le=MAX_LIMIT),
    offset:     int       = Query(0, ge=0)
):
    """👤 Listar predios asociados a un usuario"""
    try:
        return list_predios_by_usuario(usuario_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predios del usuario: {str(e)}")


# ── Rutas dinámicas después ──────────────────────────

@router.get("", response_model=list[PredioOutput])
def get_all_predios(
    limit:  int = Query(50, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0)
):
    """📋 Listar todos los predios"""
    try:
        return list_predios(limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar predios: {str(e)}")


@router.post("", response_model=PredioOutput, status_code=201)
def create_predio_endpoint(data: PredioInput):
    """➕ Crear nuevo predio"""
    try:
        return create_predio(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear predio: {str(e)}")


@router.get("/{predio_id}", response_model=PredioOutput)
def get_predio_endpoint(
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """🔍 Obtener predio por ID"""
    try:
        return get_predio_by_id(predio_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener predio: {str(e)}")


@router.put("/{predio_id}", response_model=PredioOutput)
def update_predio_endpoint(
    data:      PredioInput,
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """✏️ Actualizar predio"""
    try:
        return update_predio(predio_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar predio: {str(e)}")


@router.delete("/{predio_id}")
def delete_predio_endpoint(
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """🗑️ Eliminar predio (cascada en sensores, telemetría y alertas)"""
    try:
        return delete_predio(predio_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar predio: {str(e)}")


@router.post("/{predio_id}/usuarios/{usuario_id}", status_code=201)
def assign_usuario_endpoint(
    predio_id:  uuid.UUID = Path(..., description="ID del predio"),
    usuario_id: uuid.UUID = Path(..., description="ID del usuario")
):
    """🔗 Asignar usuario a un predio"""
    try:
        return assign_usuario_predio(usuario_id, predio_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar usuario: {str(e)}")


@router.delete("/{predio_id}/usuarios/{usuario_id}")
def remove_usuario_endpoint(
    predio_id:  uuid.UUID = Path(..., description="ID del predio"),
    usuario_id: uuid.UUID = Path(..., description="ID del usuario")
):
    """🔗 Remover acceso de usuario a un predio"""
    try:
        return remove_usuario_predio(usuario_id, predio_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al remover usuario: {str(e)}")