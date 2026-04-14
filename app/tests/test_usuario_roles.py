import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.models.usuario_model import UsuarioInput
from app.api.usuario import registro_endpoint, update_usuario_endpoint
from app.utils.auth_dependency import require_rol


def make_usuario_input(**kwargs):
    base = {
        "rol": "agronomo",
        "email": "test@example.com",
        "contrasena": "Secreto123",
        "nombre": "Test User",
        "num_telefono": None,
    }
    return UsuarioInput(**{**base, **kwargs})


def test_registro_forces_operador():
    """El endpoint de registro debe ignorar el rol enviado y forzar 'operador'."""
    data = make_usuario_input(rol="admin")

    with patch("app.api.usuario.create_usuario") as mock_create:
        mock_create.return_value = {"id": str(uuid.uuid4()), "rol": "operador", "email": data.email}

        registro_endpoint(data)

        assert mock_create.called
        passed = mock_create.call_args[0][0]
        assert getattr(passed, "rol") == "operador"


def test_require_rol_accepts_list_and_denies():
    f = require_rol(["admin", "operador"])

    user_ok = {"rol": "operador"}
    assert f(user_ok) == user_ok

    with pytest.raises(HTTPException):
        f({"rol": "agronomo"})


def test_update_denies_non_admin_for_other_user():
    """No-admin no puede actualizar otro usuario."""
    data = make_usuario_input()
    other_id = uuid.uuid4()
    current_user = {"rol": "operador", "sub": str(uuid.uuid4())}

    with pytest.raises(HTTPException):
        update_usuario_endpoint(data, usuario_id=other_id, current_user=current_user)


def test_update_preserves_role_for_non_admin_self():
    """Si un usuario no-admin actualiza su propio perfil, su rol no cambia."""
    user_id = uuid.uuid4()
    data = make_usuario_input(rol="admin")
    current_user = {"rol": "operador", "sub": str(user_id)}

    with patch("app.api.usuario.update_usuario") as mock_update:
        mock_update.return_value = {"id": str(user_id), "rol": "operador"}

        result = update_usuario_endpoint(data, usuario_id=user_id, current_user=current_user)

        assert mock_update.called
        called_args = mock_update.call_args[0]
        # llamada: update_usuario(usuario_id, data)
        passed_data = called_args[1]
        assert getattr(passed_data, "rol") == "operador"
        assert result["rol"] == "operador"


    def test_set_usuario_rol_inserts_audit():
        """Al cambiar rol, se inserta un registro en `usuario_rol_audit`."""
        user_id = uuid.uuid4()
        admin_id = str(uuid.uuid4())

        with patch("app.services.usuario_service.get_usuario_by_id", return_value={"id": str(user_id), "rol": "agronomo"}):
            with patch("app.services.usuario_service.supabase") as mock_sb:
                mock_table_usuario = MagicMock()
                mock_table_audit = MagicMock()

                def table_side_effect(name=None):
                    if name == "usuario":
                        return mock_table_usuario
                    if name == "usuario_rol_audit":
                        return mock_table_audit
                    return MagicMock()

                mock_sb.table.side_effect = table_side_effect

                # Simular respuesta de update
                mock_table_usuario.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": str(user_id), "rol": "operador"}])
                # Simular respuesta de insert en auditoría
                mock_table_audit.insert.return_value.execute.return_value = MagicMock(data=[{"id": "audit-1"}])

                from app.services.usuario_service import set_usuario_rol
                result = set_usuario_rol(user_id, "operador", admin_id=admin_id)

                assert mock_table_audit.insert.called
                assert result["rol"] == "operador"
