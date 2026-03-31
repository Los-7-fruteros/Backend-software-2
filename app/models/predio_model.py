from sqlmodel import SQLModel, Field
from datetime import datetime, timezone  
from typing import Optional
import uuid


class Predio(SQLModel, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str                              # ← NOT NULL en schema, obligatorio
    ubicacion: Optional[str] = None          # ← TEXT sin NOT NULL en schema
    tipo_cultivo: Optional[str] = None       # ← TEXT sin NOT NULL en schema
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  


class PredioInput(SQLModel):
    nombre: str
    ubicacion: Optional[str] = None
    tipo_cultivo: Optional[str] = None


class PredioOutput(SQLModel):               
    id: uuid.UUID
    nombre: str
    ubicacion: Optional[str]
    tipo_cultivo: Optional[str]
    created_at: datetime