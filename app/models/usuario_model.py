from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import field_validator, EmailStr  # ← EmailStr nuevo
from typing import Optional
from app.utils.sanitizers import sanitizar_string, sanitizar_email
import uuid


class Usuario(SQLModel, table=False):
    id:              uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rol:             str
    email:           str
    hash_contrasena: str
    nombre:          str
    num_telefono:    Optional[str] = None
    created_at:      datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UsuarioInput(SQLModel):
    rol:          str
    email:        str
    contrasena:   str
    nombre:       str
    num_telefono: Optional[str] = None

    @field_validator("nombre", "rol", mode="before")
    @classmethod
    def sanitizar_strings(cls, v, info):
        return sanitizar_string(v, info.field_name)

    @field_validator("email", mode="before")
    @classmethod
    def sanitizar_email_field(cls, v):
        return sanitizar_email(v)

    @field_validator("num_telefono", mode="before")
    @classmethod
    def sanitizar_telefono(cls, v):
        if v is not None:
            # Solo permitir números, +, - y espacios
            if not re.match(r"^[\d\s\+\-]{7,15}$", v):
                raise ValueError("Formato de teléfono inválido")
        return v


class UsuarioOutput(SQLModel):
    id:           uuid.UUID
    rol:          str
    email:        str
    nombre:       str
    num_telefono: Optional[str]
    created_at:   datetime