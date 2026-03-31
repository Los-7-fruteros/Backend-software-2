from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_current_usuario
from typing import Dict, Any

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """
    Dependencia FastAPI para proteger rutas.
    Uso: def mi_endpoint(user=Depends(get_current_user))
    """
    return get_current_usuario(credentials.credentials)


def require_rol(rol: str):
    """
    Dependencia para proteger rutas por rol.
    Uso: def mi_endpoint(user=Depends(require_rol("admin")))
    """
    def verificar_rol(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("rol") != rol:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return user
    return verificar_rol