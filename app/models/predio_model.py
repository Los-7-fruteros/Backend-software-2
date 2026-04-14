from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator
from typing import Optional
from app.utils.sanitizers import sanitizar_string
import uuid


class Predio(SQLModel, table=False):
    id:           uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre:       str
    ubicacion:    Optional[str] = None
    tipo_cultivo: Optional[str] = None
    created_at:   datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PredioInput(SQLModel):
    nombre:       str
    ubicacion:    Optional[str] = None
    tipo_cultivo: Optional[str] = None

    @field_validator("nombre", "ubicacion", "tipo_cultivo", mode="before")
    @classmethod
    def sanitizar_strings(cls, v, info):
        if v is not None:
            return sanitizar_string(v, info.field_name)
        return v


class PredioOutput(SQLModel):
    id:           uuid.UUID
    nombre:       str
    ubicacion:    Optional[str]
    tipo_cultivo: Optional[str]
    created_at:   datetime