from sqlmodel import SQLModel, Field
from datetime import datetime, timezone  # ← fix 1: importar clase, no módulo
from typing import Optional
import uuid


class Usuario(SQLModel, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rol: str                                 # ← NOT NULL en schema
    email: str                               # ← NOT NULL + UNIQUE en schema
    hash_contrasena: str                     # ← str es correcto para bcrypt
    nombre: str                              # ← NOT NULL en schema
    num_telefono: Optional[str] = None       # ← TEXT sin NOT NULL en schema
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # ← fix 2: callable


class UsuarioInput(SQLModel):
    rol: str
    email: str
    contrasena: str                          # ← texto plano, se hashea en el servicio
    nombre: str
    num_telefono: Optional[str] = None


class UsuarioOutput(SQLModel):              # ← fix 3: hereda de SQLModel, no de Usuario
    id: uuid.UUID
    rol: str
    email: str
    nombre: str
    num_telefono: Optional[str]
    created_at: datetime
    # hash_contrasena ausente intencionalmente ✅