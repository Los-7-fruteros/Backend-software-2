from sqlmodel import SQLModel, Field
from datetime import datetime, timezone 
from typing import Optional
import uuid


class Sensor(SQLModel, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sector: Optional[str] = None         # ← TEXT sin NOT NULL en schema
    device_id: Optional[str] = None      # ← TEXT sin NOT NULL en schema
    predio_id: uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  


class SensorInput(SQLModel):
    sector: Optional[str] = None
    device_id: Optional[str] = None     
    predio_id: uuid.UUID


class SensorOutput(SQLModel):           
    id: uuid.UUID
    sector: Optional[str]
    device_id: Optional[str]
    predio_id: uuid.UUID
    created_at: datetime