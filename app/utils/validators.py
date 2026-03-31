import math
from pydantic import field_validator


def validate_no_nan(v):
    """
    Rechaza NaN e infinitos que puedan venir de sensores defectuosos.
    Reutilizable en cualquier modelo con campos numéricos.
    """
    if v is not None:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Valor inválido: NaN o infinito no permitido")
    return v