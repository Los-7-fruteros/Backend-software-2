from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_current_usuario
from typing import Dict, Any

bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Token JWT obtenido desde /api/auth/login",
    auto_error=True  # ← retorna 403 automáticamente si no hay token
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """
    Dependencia FastAPI para proteger rutas con JWT.
    Valida firma, expiración y payload completo.
    Uso: dependencies=[Depends(get_current_user)]
    """
    return get_current_usuario(credentials.credentials)


def require_rol(rol: str):
    """
    Dependencia para proteger rutas por rol.
    Uso: Depends(require_rol("admin"))
    """
    def verificar_rol(
        user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        if user.get("rol") != rol:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere rol '{rol}'."
            )
        return user
    return verificar_rol


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer(auto_error=False)  # ← no falla si no hay token
    )
) -> Dict[str, Any] | None:
    """
    Dependencia opcional — no falla si no hay token.
    Útil para endpoints públicos que muestran más info si hay sesión.
    """
    if not credentials:
        return None
    return get_current_usuario(credentials.credentials)