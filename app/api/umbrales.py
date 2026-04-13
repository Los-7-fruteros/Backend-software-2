from fastapi import APIRouter, HTTPException, Path, Depends
from app.utils.auth_dependency import get_current_user
from app.models.umbrales_model import UmbralInput, UmbralOutput
from app.services.umbrales_service import (
    get_umbrales_by_predio,
    get_umbral_by_id,
    create_umbral,
    update_umbral,
    delete_umbral
)
import uuid

router = APIRouter(
    prefix="/api/umbrales",
    tags=["Umbrales"],
    dependencies=[Depends(get_current_user)]  # ← protege todo el router
)



# ── Rutas estáticas primero ──────────────────────────

@router.get("/predio/{predio_id}", response_model=UmbralOutput)
def get_umbrales_by_predio_endpoint(
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """📋 Obtener umbrales configurados para un predio"""
    try:
        umbrales = get_umbrales_by_predio(predio_id)
        if not umbrales:
            raise HTTPException(
                status_code=404,
                detail=f"No hay umbrales configurados para el predio {predio_id}"
            )
        return umbrales
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener umbrales: {str(e)}")


@router.post("/predio/{predio_id}", response_model=UmbralOutput, status_code=201)
def create_umbral_endpoint(
    data:      UmbralInput,
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """➕ Crear umbrales para un predio"""
    try:
        # Asegurar que el predio_id del path y del body coincidan
        data.predio_id = predio_id
        return create_umbral(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear umbral: {str(e)}")


@router.put("/predio/{predio_id}", response_model=UmbralOutput)
def update_umbral_endpoint(
    data:      UmbralInput,
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """✏️ Actualizar umbrales de un predio"""
    try:
        return update_umbral(predio_id, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar umbral: {str(e)}")


@router.delete("/predio/{predio_id}")
def delete_umbral_endpoint(
    predio_id: uuid.UUID = Path(..., description="ID del predio")
):
    """🗑️ Eliminar umbrales de un predio"""
    try:
        return delete_umbral(predio_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar umbral: {str(e)}")


# ── Ruta dinámica después ──────────────────────────

@router.get("/{umbral_id}", response_model=UmbralOutput)
def get_umbral_by_id_endpoint(
    umbral_id: uuid.UUID = Path(..., description="ID del umbral")
):
    """🔍 Obtener umbral por ID"""
    try:
        return get_umbral_by_id(umbral_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener umbral: {str(e)}")