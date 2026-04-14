from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.db.supabase_client import supabase
from app.services.usuario_service import get_usuario_by_email
from app.utils.logger import logger
from typing import Dict, Any
import jwt
import os
import uuid

# ── Configuración JWT ─────────────────────
SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM          = "HS256"
TOKEN_EXPIRY_HOURS = 24

REQUIRED_PAYLOAD_FIELDS = {"sub", "rol", "email"}


# ──────────────────────────────────────────
# HELPERS PRIVADOS
# ──────────────────────────────────────────

def _crear_token(payload: Dict[str, Any]) -> str:
    """Generar JWT firmado con expiración."""
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decodificar_token(token: str) -> Dict[str, Any]:
    """Decodificar y validar JWT con campos obligatorios."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("🔐 Token expirado rechazado")
        raise HTTPException(
            status_code=401,
            detail="Token expirado. Por favor inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidSignatureError:
        logger.warning("🔐 Token con firma inválida rechazado")
        raise HTTPException(
            status_code=401,
            detail="Token con firma inválida.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.DecodeError:
        logger.warning("🔐 Token malformado rechazado")
        raise HTTPException(
            status_code=401,
            detail="Token malformado.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"🔐 Token inválido: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validar campos obligatorios
    campos_faltantes = REQUIRED_PAYLOAD_FIELDS - payload.keys()
    if campos_faltantes:
        raise HTTPException(
            status_code=401,
            detail=f"Token inválido: faltan campos {campos_faltantes}.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validar sub como UUID
    try:
        uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido: identificador de usuario malformado.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload


# ──────────────────────────────────────────
# AUTH CON SUPABASE
# ──────────────────────────────────────────

def login(email: str, contrasena: str) -> Dict[str, Any]:
    """
    Verifica credenciales usando Supabase Auth.
    Supabase compara la contraseña contra su hash interno.
    Si es válida, genera nuestro propio JWT.
    """
    try:
        # ✅ Supabase verifica la contraseña internamente (bcrypt)
        auth_response = supabase.auth.sign_in_with_password({
            "email":    email,
            "password": contrasena
        })
    except Exception:
        # Mismo mensaje para email y contraseña incorrectos
        # evita enumeración de usuarios
        logger.warning(f"🔐 Login fallido | email={email}")
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not auth_response.user:
        logger.warning(f"🔐 Login fallido | email={email}")
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Obtener datos adicionales del usuario desde nuestra tabla
    usuario = get_usuario_by_email(email)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en el sistema.")

    # Generar nuestro JWT propio
    token = _crear_token({
        "sub":   usuario["id"],
        "rol":   usuario["rol"],
        "email": usuario["email"]
    })

    logger.info(f"🔐 Login exitoso | email={email}")
    return {
        "access_token": token,
        "token_type":   "bearer",
        "expires_in":   TOKEN_EXPIRY_HOURS * 3600,
        "usuario": {
            "id":     usuario["id"],
            "nombre": usuario["nombre"],
            "email":  usuario["email"],
            "rol":    usuario["rol"]
        }
    }


def get_current_usuario(token: str) -> Dict[str, Any]:
    """Decodificar token y retornar payload validado."""
    return _decodificar_token(token)