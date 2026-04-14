from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator, model_validator
from typing import Optional
from app.utils.validators import validate_no_nan
import uuid


class Telemetria(SQLModel, table=False):
    """Registro de datos telemétricos enviados por un módulo de sensor"""
    id:           uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    humedad:      Optional[float] = None
    temperatura:  Optional[float] = None
    ph:           Optional[float] = None
    voltaje:      Optional[float] = None
    sensor_id:    uuid.UUID = Field(..., description="ID del módulo de sensor que envía los datos")
    created_at:   datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetriaInput(SQLModel):
    """Payload de entrada para datos telemétricos - soporta identificación por sensor_id o device_id"""
    humedad:      Optional[float] = Field(None, ge=0,   le=100,  description="Humedad relativa (%)")
    temperatura:  Optional[float] = Field(None, ge=-50, le=100,  description="Temperatura (°C)")
    ph:           Optional[float] = Field(None, ge=0,   le=14,   description="Escala de pH")
    voltaje:      Optional[float] = Field(None, ge=0,   le=30,   description="Voltaje del sensor (V)")
    sensor_id:    Optional[uuid.UUID] = Field(None, description="ID único del módulo de sensor (preferido)")
    device_id:    Optional[str] = Field(None, description="ID del dispositivo físico (alternativa a sensor_id)")

    # ── Validators de campo ──────────────────────────
    @field_validator("humedad", "temperatura", "ph", "voltaje", mode="before")
    @classmethod
    def validar_no_nan(cls, v):
        """Rechaza NaN e infinitos antes de aplicar ge/le."""
        return validate_no_nan(v)

    # ── Validator de modelo ──────────────────────────
    @model_validator(mode="after")
    def validadores_telemetria(self):
        """
        Valida que:
        1. Al menos una medición tenga valor
        2. Se proporcione identificación del sensor (sensor_id ó device_id)
        """
        # Validar que al menos una medición existe
        campos_medicion = [self.humedad, self.temperatura, self.ph, self.voltaje]
        if all(v is None for v in campos_medicion):
            raise ValueError("Debe enviar al menos un campo de medición (humedad, temperatura, ph o voltaje)")
        
        # Validar que se proporcione identificación del sensor
        if not self.sensor_id and not self.device_id:
            raise ValueError("Debe proporcionar identificación del módulo de sensor usando 'sensor_id' (UUID) o 'device_id' (string)")
        
        return self


class TelemetriaOutput(SQLModel):
    """Respuesta con datos telemétricos almacenados"""
    id:           uuid.UUID
    humedad:      Optional[float]
    temperatura:  Optional[float]
    ph:           Optional[float]
    voltaje:      Optional[float]
    sensor_id:    uuid.UUID
    created_at:   datetime