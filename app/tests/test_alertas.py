import pytest
import uuid
from unittest.mock import patch
from fastapi import HTTPException
from app.models.alertas_model import AlertaInput
from conftest import SENSOR_ID, ALERTA_ID


# ── Helpers ───────────────────────────────────────

def make_input(**kwargs):
    base = {"tipo": "humedad", "valor": 95.0, "mensaje": "Humedad alta", "sensor_id": SENSOR_ID}
    return AlertaInput(**{**base, **kwargs})


# ── Tests de creación ─────────────────────────────

class TestCreateAlerta:

    def test_create_exitoso(self, sensor_data, alerta_data, mock_supabase_response):
        """Creación exitosa cuando el sensor existe."""
        with patch("app.services.alertas_service.get_sensor_by_id", return_value=sensor_data), \
             patch("app.services.alertas_service.supabase") as mock_sb:

            mock_sb.table().insert().execute.return_value = mock_supabase_response([alerta_data])

            from app.services.alertas_service import create_alerta
            result = create_alerta(make_input())

            assert result["tipo"] == "humedad"
            assert result["valor"] == 95.0

    def test_create_sensor_no_existe(self):
        """Lanza 404 si el sensor no existe."""
        with patch("app.services.alertas_service.get_sensor_by_id", return_value=None):
            from app.services.alertas_service import create_alerta
            with pytest.raises(HTTPException) as exc:
                create_alerta(make_input())
            assert exc.value.status_code == 404

    def test_create_error_supabase(self, sensor_data, mock_supabase_response):
        """Lanza 500 si Supabase no retorna data."""
        with patch("app.services.alertas_service.get_sensor_by_id", return_value=sensor_data), \
             patch("app.services.alertas_service.supabase") as mock_sb:

            mock_sb.table().insert().execute.return_value = mock_supabase_response([])

            from app.services.alertas_service import create_alerta
            with pytest.raises(HTTPException) as exc:
                create_alerta(make_input())
            assert exc.value.status_code == 500


# ── Tests de consulta ─────────────────────────────

class TestGetAlerta:

    def test_get_by_id_exitoso(self, alerta_data, mock_supabase_response):
        """Retorna alerta cuando existe."""
        with patch("app.services.alertas_service.supabase") as mock_sb:
            mock_sb.table().select().eq().execute.return_value = \
                mock_supabase_response([alerta_data])

            from app.services.alertas_service import get_alerta_by_id
            result = get_alerta_by_id(ALERTA_ID)

            assert result["id"] == str(ALERTA_ID)

    def test_get_by_id_no_existe(self, mock_supabase_response):
        """Lanza 404 si la alerta no existe."""
        with patch("app.services.alertas_service.supabase") as mock_sb:
            mock_sb.table().select().eq().execute.return_value = \
                mock_supabase_response([])

            from app.services.alertas_service import get_alerta_by_id
            with pytest.raises(HTTPException) as exc:
                get_alerta_by_id(ALERTA_ID)
            assert exc.value.status_code == 404


# ── Tests de validación Pydantic ──────────────────

class TestAlertaInputValidacion:

    def test_tipo_invalido(self):
        """Rechaza tipos no definidos."""
        with pytest.raises(Exception):
            AlertaInput(tipo="viento", valor=10.0, sensor_id=SENSOR_ID)

    def test_mensaje_vacio(self):
        """Rechaza mensajes vacíos."""
        with pytest.raises(Exception):
            AlertaInput(tipo="humedad", valor=10.0, mensaje="   ", sensor_id=SENSOR_ID)

    def test_tipo_valido(self):
        """Acepta tipos válidos."""
        data = AlertaInput(tipo="temperatura", valor=50.0, sensor_id=SENSOR_ID)
        assert data.tipo == "temperatura"