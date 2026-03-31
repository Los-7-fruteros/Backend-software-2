from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator, model_validator
from typing import Optional
from app.utils.validators import validate_no_nan
import uuid


class Telemetria(SQLModel, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    humedad:     Optional[float] = None
    temperatura: Optional[float] = None
    ph:          Optional[float] = None
    voltaje:     Optional[float] = None
    sensor_id:   uuid.UUID
    created_at:  datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetriaInput(SQLModel):
    humedad:     Optional[float] = Field(None, ge=0,   le=100,  description="Humedad relativa (%)")
    temperatura: Optional[float] = Field(None, ge=-50, le=100,  description="Temperatura (°C)")
    ph:          Optional[float] = Field(None, ge=0,   le=14,   description="Escala de pH")
    voltaje:     Optional[float] = Field(None, ge=0,   le=30,   description="Voltaje del sensor (V)")
    sensor_id:   uuid.UUID

    # ── Validators de campo ──────────────────────────
    @field_validator("humedad", "temperatura", "ph", "voltaje", mode="before")
    @classmethod
    def validar_no_nan(cls, v):
        """Rechaza NaN e infinitos antes de aplicar ge/le."""
        return validate_no_nan(v)

    # ── Validator de modelo ──────────────────────────
    @model_validator(mode="after")
    def al_menos_un_campo(self):
        """Al menos una medición debe venir con valor."""
        campos = [self.humedad, self.temperatura, self.ph, self.voltaje]
        if all(v is None for v in campos):
            raise ValueError("Debe enviar al menos un campo de medición (humedad, temperatura, ph o voltaje)")
        return self


class TelemetriaOutput(SQLModel):
    id:          uuid.UUID
    humedad:     Optional[float]
    temperatura: Optional[float]
    ph:          Optional[float]
    voltaje:     Optional[float]
    sensor_id:   uuid.UUID
    created_at:  datetime