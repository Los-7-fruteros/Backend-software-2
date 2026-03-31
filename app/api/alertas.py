from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from app.models.alertas_model import AlertaInput, AlertaOutput
from app.services.alertas_service import (
    get_alerta_by_id,
    list_alertas,
    list_alertas_by_predio,
    create_alerta,
    delete_alerta,
    MAX_LIMIT
)
import uuid

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])


# ── Rutas estáticas primero ──────────────────────────

@router.get("/predio/{predio_id}", response_model=list[AlertaOutput])
def get_alertas_by_predio(
    predio_id: uuid.UUID = Path(..., description="ID del predio"),
    limit:     int       = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int       = Query(0, ge=0)
):
    """📍 Listar todas las alertas de un predio"""
    try:
        return list_alertas_by_predio(predio_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener alertas del predio: {str(e)}")


# ── Rutas dinámicas después ──────────────────────────

@router.get("", response_model=list[AlertaOutput])
def get_all_alertas(
    sensor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por sensor"),
    limit:     int                  = Query(50, ge=1, le=MAX_LIMIT),
    offset:    int                  = Query(0, ge=0)
):
    """📋 Listar alertas con filtros opcionales"""
    try:
        return list_alertas(sensor_id=sensor_id, limit=limit, offset=offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar alertas: {str(e)}")


@router.post("", response_model=AlertaOutput, status_code=201)
def create_alerta_endpoint(data: AlertaInput):
    """🚨 Crear alerta manualmente"""
    try:
        return create_alerta(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear alerta: {str(e)}")


@router.get("/{alerta_id}", response_model=AlertaOutput)
def get_alerta_endpoint(
    alerta_id: uuid.UUID = Path(..., description="ID de la alerta")
):
    """🔍 Obtener alerta por ID"""
    try:
        return get_alerta_by_id(alerta_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener alerta: {str(e)}")


@router.delete("/{alerta_id}")
def delete_alerta_endpoint(
    alerta_id: uuid.UUID = Path(..., description="ID de la alerta")
):
    """🗑️ Eliminar alerta por ID"""
    try:
        return delete_alerta(alerta_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar alerta: {str(e)}")