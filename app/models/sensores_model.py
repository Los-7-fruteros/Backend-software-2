from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator
from typing import Optional
from app.utils.sanitizers import sanitizar_string
import uuid


class Sensor(SQLModel, table=False):
    id:         uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sector:     Optional[str] = None
    device_id:  Optional[str] = None
    predio_id:  uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SensorInput(SQLModel):
    sector:    Optional[str] = None
    device_id: Optional[str] = None
    predio_id: uuid.UUID

    @field_validator("sector", "device_id", mode="before")
    @classmethod
    def sanitizar_strings(cls, v, info):
        if v is not None:
            return sanitizar_string(v, info.field_name)
        return v


class SensorOutput(SQLModel):
    id:         uuid.UUID
    sector:     Optional[str]
    device_id:  Optional[str]
    predio_id:  uuid.UUID
    created_at: datetime