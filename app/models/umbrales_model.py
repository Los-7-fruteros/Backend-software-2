from sqlmodel import SQLModel, Field
from datetime import datetime, timezone  
from pydantic import field_validator, model_validator
from typing import Optional
from app.utils.validators import validate_no_nan
import uuid


class Umbral(SQLModel, table=False):
    id:              uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    humedad_min:     Optional[float] = None   # ← NUMERIC sin NOT NULL en schema
    humedad_max:     Optional[float] = None
    temperatura_min: Optional[float] = None
    temperatura_max: Optional[float] = None
    ph_min:          Optional[float] = None
    ph_max:          Optional[float] = None
    voltaje_min:     Optional[float] = None   # ← solo min, sin max en schema
    predio_id:       uuid.UUID
    created_at:      datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  


class UmbralInput(SQLModel):
    humedad_min:     Optional[float] = Field(None, ge=0,   le=100,  description="Humedad mínima (%)")
    humedad_max:     Optional[float] = Field(None, ge=0,   le=100,  description="Humedad máxima (%)")
    temperatura_min: Optional[float] = Field(None, ge=-50, le=100,  description="Temperatura mínima (°C)")
    temperatura_max: Optional[float] = Field(None, ge=-50, le=100,  description="Temperatura máxima (°C)")
    ph_min:          Optional[float] = Field(None, ge=0,   le=14,   description="pH mínimo")
    ph_max:          Optional[float] = Field(None, ge=0,   le=14,   description="pH máximo")
    voltaje_min:     Optional[float] = Field(None, ge=0,   le=30,   description="Voltaje mínimo (V)")
    predio_id:       uuid.UUID

    # ── Validators de campo ──────────────────────────
    @field_validator(
        "humedad_min", "humedad_max",
        "temperatura_min", "temperatura_max",
        "ph_min", "ph_max",
        "voltaje_min",
        mode="before"
    )
    @classmethod
    def validar_no_nan(cls, v):
        """Rechaza NaN e infinitos."""
        return validate_no_nan(v)

    # ── Validators de modelo ─────────────────────────
    @model_validator(mode="after")
    def validar_rangos_coherentes(self):
        """
        Verifica que min < max en cada variable.
        Evita configuraciones imposibles como humedad_min=80, humedad_max=20.
        """
        pares = [
            ("humedad_min",     "humedad_max",     "Humedad"),
            ("temperatura_min", "temperatura_max", "Temperatura"),
            ("ph_min",          "ph_max",          "pH"),
        ]
        for campo_min, campo_max, nombre in pares:
            minimo = getattr(self, campo_min)
            maximo = getattr(self, campo_max)
            if minimo is not None and maximo is not None and minimo >= maximo:
                raise ValueError(
                    f"{nombre}: el valor mínimo ({minimo}) debe ser menor al máximo ({maximo})"
                )
        return self


class UmbralOutput(SQLModel):           
    id:              uuid.UUID
    humedad_min:     Optional[float]
    humedad_max:     Optional[float]
    temperatura_min: Optional[float]
    temperatura_max: Optional[float]
    ph_min:          Optional[float]
    ph_max:          Optional[float]
    voltaje_min:     Optional[float]
    predio_id:       uuid.UUID
    created_at:      datetime