from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator
from typing import Optional
from app.utils.validators import validate_no_nan
import uuid


TIPOS_VALIDOS = {"humedad", "temperatura", "ph", "voltaje"}


class Alerta(SQLModel, table=False):
    id:         uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tipo:       str
    valor:      Optional[float] = None
    mensaje:    Optional[str]   = None
    sensor_id:  uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertaInput(SQLModel):
    tipo:      str
    valor:     Optional[float] = Field(None, description="Valor que disparó la alerta")
    mensaje:   Optional[str]   = None
    sensor_id: uuid.UUID

    # ── Validators de campo ──────────────────────────
    @field_validator("valor", mode="before")
    @classmethod
    def validar_no_nan(cls, v):
        """Rechaza NaN e infinitos."""
        return validate_no_nan(v)

    @field_validator("tipo", mode="before")
    @classmethod
    def validar_tipo(cls, v):
        """Solo acepta tipos de alerta conocidos."""
        if v not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido: '{v}'. Válidos: {TIPOS_VALIDOS}")
        return v

    @field_validator("mensaje", mode="before")
    @classmethod
    def validar_mensaje(cls, v):
        """Evita mensajes vacíos o solo espacios."""
        if v is not None and not v.strip():
            raise ValueError("El mensaje no puede estar vacío")
        return v


class AlertaOutput(SQLModel):
    id:         uuid.UUID
    tipo:       str
    valor:      Optional[float]
    mensaje:    Optional[str]
    sensor_id:  uuid.UUID
    created_at: datetime