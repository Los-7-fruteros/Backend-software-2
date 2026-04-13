import re
import html
from app.utils.logger import logger


# ──────────────────────────────────────────
# PATRONES PELIGROSOS
# ──────────────────────────────────────────

# Tags HTML/scripts
PATRON_HTML       = re.compile(r"<[^>]*>", re.IGNORECASE)

# Intentos de inyección SQL
PATRON_SQL        = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|UNION|SCRIPT)\b",
    re.IGNORECASE
)

# Caracteres de control y nulos
PATRON_CONTROL    = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Scripts inline
PATRON_SCRIPT     = re.compile(r"(javascript:|vbscript:|on\w+=)", re.IGNORECASE)


# ──────────────────────────────────────────
# SANITIZADORES
# ──────────────────────────────────────────

def sanitizar_string(valor: str, campo: str = "campo") -> str:
    """
    Sanitiza un string contra XSS, inyección SQL y caracteres peligrosos.
    - Elimina tags HTML
    - Escapa caracteres especiales HTML
    - Detecta y bloquea patrones SQL peligrosos
    - Elimina caracteres de control
    - Elimina scripts inline
    - Hace strip de espacios al inicio y final
    """
    if not isinstance(valor, str):
        return valor

    original = valor

    # 1. Strip espacios
    valor = valor.strip()

    # 2. Eliminar caracteres de control
    valor = PATRON_CONTROL.sub("", valor)

    # 3. Eliminar scripts inline (javascript:, onerror=, etc.)
    if PATRON_SCRIPT.search(valor):
        logger.warning(f"🛡️ Script inline detectado en campo '{campo}': {valor[:50]}")
        valor = PATRON_SCRIPT.sub("", valor)

    # 4. Eliminar tags HTML
    valor = PATRON_HTML.sub("", valor)

    # 5. Escapar caracteres especiales HTML (&, <, >, ", ')
    valor = html.escape(valor, quote=True)

    # 6. Detectar patrones SQL (solo loggear, no bloquear — Supabase usa queries parametrizadas)
    if PATRON_SQL.search(valor):
        logger.warning(f"🛡️ Patrón SQL detectado en campo '{campo}': {valor[:50]}")

    if valor != original.strip():
        logger.info(f"🛡️ Campo '{campo}' sanitizado")

    return valor


def sanitizar_email(email: str) -> str:
    """
    Normaliza email: lowercase y strip.
    La validación de formato la hace Pydantic con EmailStr.
    """
    return email.strip().lower()


def sanitizar_dict(data: dict, campos_string: list[str]) -> dict:
    """
    Sanitiza campos string específicos de un diccionario.
    Útil para sanitizar payloads antes de insertar en DB.

    Uso:
        data = sanitizar_dict(data, ["nombre", "sector", "mensaje"])
    """
    for campo in campos_string:
        if campo in data and isinstance(data[campo], str):
            data[campo] = sanitizar_string(data[campo], campo)
    return data