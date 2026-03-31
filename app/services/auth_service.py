from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.services.usuario_service import get_usuario_by_email
from app.utils.logger import logger
from typing import Dict, Any
import bcrypt
import jwt
import os

# ── Configuración JWT ─────────────────────
SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM   = "HS256"
TOKEN_EXPIRY_HOURS = 24


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────

def _verificar_contrasena(contrasena: str, hash_contrasena: str) -> bool:
    """Comparar contraseña plana contra hash bcrypt."""
    return bcrypt.checkpw(
        contrasena.encode("utf-8"),
        hash_contrasena.encode("utf-8")
    )


def _crear_token(payload: Dict[str, Any]) -> str:
    """Generar JWT firmado con expiración."""
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decodificar_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar JWT.
    Lanza 401 si expiró o es inválido.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ──────────────────────────────────────────
# AUTH PÚBLICO
# ──────────────────────────────────────────

def login(email: str, contrasena: str) -> Dict[str, Any]:
    """
    Verificar credenciales y retornar JWT.
    Lanza 401 si el email no existe o la contraseña no coincide.
    """
    usuario = get_usuario_by_email(email)

    # Mismo mensaje para email y contraseña incorrectos
    # evita enumerar usuarios existentes
    if not usuario or not _verificar_contrasena(contrasena, usuario["hash_contrasena"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = _crear_token({
        "sub":  usuario["id"],
        "rol":  usuario["rol"],
        "email": usuario["email"]
    })

    logger.info(f"🔐 Login exitoso | email={email}")
    return {
        "access_token": token,
        "token_type":   "bearer",
        "usuario": {
            "id":     usuario["id"],
            "nombre": usuario["nombre"],
            "email":  usuario["email"],
            "rol":    usuario["rol"]
        }
    }


def get_current_usuario(token: str) -> Dict[str, Any]:
    """Decodificar token y retornar payload del usuario."""
    return _decodificar_token(token)