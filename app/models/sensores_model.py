from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator
from typing import Optional
from app.utils.sanitizers import sanitizar_string
import uuid


class Sensor(SQLModel, table=False):
    """Modelo de Módulo de Sensor - representa un dispositivo de monitoreo dentro de un predio"""
    id:          uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre:      str = Field(..., description="Nombre del módulo (ej: 'Módulo Zona A', 'Sensor Norte')")
    nombre_zona: Optional[str] = Field(None, description="Zona de cultivo que monitorea (ej: 'Campo de tomates')")
    device_id:   Optional[str] = Field(None, description="ID único del dispositivo físico")
    predio_id:   uuid.UUID = Field(..., description="ID del predio (campo) que contiene este módulo")
    created_at:  datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SensorInput(SQLModel):
    nombre:      str = Field(..., min_length=1, max_length=255, description="Nombre descriptivo del módulo")
    nombre_zona: Optional[str] = Field(None, max_length=255, description="Zona de cultivo a monitorear")
    device_id:   Optional[str] = Field(None, max_length=100, description="ID del dispositivo físico (único en el sistema)")
    predio_id:   uuid.UUID = Field(..., description="ID del predio que contendrá este módulo")

    @field_validator("nombre", "nombre_zona", "device_id", mode="before")
    @classmethod
    def sanitizar_strings(cls, v, info):
        if v is not None:
            return sanitizar_string(v, info.field_name)
        return v


class SensorOutput(SQLModel):
    id:          uuid.UUID
    nombre:      str
    nombre_zona: Optional[str]
    device_id:   Optional[str]
    predio_id:   uuid.UUID
    created_at:  datetime