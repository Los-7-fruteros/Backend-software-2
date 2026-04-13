from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.services.usuario_service import get_usuario_by_email
from app.utils.logger import logger
from typing import Dict, Any
import bcrypt
import jwt
import os

# ── Configuración JWT ─────────────────────
SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM          = "HS256"
TOKEN_EXPIRY_HOURS = 24

# ── Campos obligatorios en el payload ────
REQUIRED_PAYLOAD_FIELDS = {"sub", "rol", "email"}


# ──────────────────────────────────────────
# HELPERS PRIVADOS
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
    payload["iat"] = datetime.now(timezone.utc)  # ← issued at: cuándo fue emitido
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decodificar_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar JWT.
    Valida firma, expiración y campos obligatorios del payload.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("🔐 Token expirado rechazado")
        raise HTTPException(
            status_code=401,
            detail="Token expirado. Por favor inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"}  # ← estándar OAuth2
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

    # ── Validar campos obligatorios del payload ──
    campos_faltantes = REQUIRED_PAYLOAD_FIELDS - payload.keys()
    if campos_faltantes:
        logger.warning(f"🔐 Token sin campos requeridos: {campos_faltantes}")
        raise HTTPException(
            status_code=401,
            detail=f"Token inválido: faltan campos {campos_faltantes}.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # ── Validar que sub sea un UUID válido ──
    import uuid
    try:
        uuid.UUID(payload["sub"])
    except ValueError:
        logger.warning(f"🔐 Token con sub inválido: {payload['sub']}")
        raise HTTPException(
            status_code=401,
            detail="Token inválido: identificador de usuario malformado.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload


# ──────────────────────────────────────────
# AUTH PÚBLICO
# ──────────────────────────────────────────

def login(email: str, contrasena: str) -> Dict[str, Any]:
    """
    Verificar credenciales y retornar JWT.
    Mismo mensaje para email y contraseña incorrectos
    para evitar enumeración de usuarios.
    """
    usuario = get_usuario_by_email(email)

    if not usuario or not _verificar_contrasena(contrasena, usuario["hash_contrasena"]):
        logger.warning(f"🔐 Intento de login fallido | email={email}")
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = _crear_token({
        "sub":   usuario["id"],
        "rol":   usuario["rol"],
        "email": usuario["email"]
    })

    logger.info(f"🔐 Login exitoso | email={email}")
    return {
        "access_token": token,
        "token_type":   "bearer",
        "expires_in":   TOKEN_EXPIRY_HOURS * 3600,  # ← en segundos
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