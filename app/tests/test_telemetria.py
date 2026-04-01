import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.models.telemetria_model import TelemetriaInput
from conftest import SENSOR_ID, PREDIO_ID


# ── Helpers ───────────────────────────────────────

def make_input(**kwargs):
    base = {"humedad": 65.0, "temperatura": 22.0, "ph": 7.0, "voltaje": 12.0, "sensor_id": SENSOR_ID}
    return TelemetriaInput(**{**base, **kwargs})


# ── Tests de inserción ────────────────────────────

class TestInsertTelemetryData:

    def test_insert_exitoso(self, sensor_data, telemetria_data, mock_supabase_response):
        """Inserción exitosa cuando el sensor existe."""
        with patch("app.services.telemetria_service.get_sensor_by_id", return_value=sensor_data), \
             patch("app.services.telemetria_service.supabase") as mock_sb, \
             patch("app.services.telemetria_service.check_umbrales", return_value=[]):

            mock_sb.table().insert().execute.return_value = mock_supabase_response([telemetria_data])

            from app.services.telemetria_service import insert_telemetry_data
            result = insert_telemetry_data(SENSOR_ID, make_input())

            assert result["sensor_id"] == str(SENSOR_ID)
            assert result["humedad"] == 65.0

    def test_insert_sensor_no_existe(self):
        """Lanza 404 si el sensor no existe."""
        with patch("app.services.telemetria_service.get_sensor_by_id", return_value=None):
            from app.services.telemetria_service import insert_telemetry_data
            with pytest.raises(HTTPException) as exc:
                insert_telemetry_data(SENSOR_ID, make_input())
            assert exc.value.status_code == 404

    def test_insert_error_supabase(self, sensor_data, mock_supabase_response):
        """Lanza 500 si Supabase no retorna data."""
        with patch("app.services.telemetria_service.get_sensor_by_id", return_value=sensor_data), \
             patch("app.services.telemetria_service.supabase") as mock_sb, \
             patch("app.services.telemetria_service.check_umbrales", return_value=[]):

            mock_sb.table().insert().execute.return_value = mock_supabase_response([])

            from app.services.telemetria_service import insert_telemetry_data
            with pytest.raises(HTTPException) as exc:
                insert_telemetry_data(SENSOR_ID, make_input())
            assert exc.value.status_code == 500


# ── Tests de listado ──────────────────────────────

class TestListTelemetry:

    def test_list_sin_filtros(self, telemetria_data, mock_supabase_response):
        """Lista telemetría sin filtros."""
        with patch("app.services.telemetria_service.supabase") as mock_sb:
            mock_sb.table().select().range().order().execute.return_value = \
                mock_supabase_response([telemetria_data])

            from app.services.telemetria_service import list_telemetry
            result = list_telemetry()

            assert len(result) == 1
            assert result[0]["humedad"] == 65.0

    def test_list_limit_maximo(self, mock_supabase_response):
        """El limit se techa en MAX_LIMIT."""
        with patch("app.services.telemetria_service.supabase") as mock_sb:
            mock_sb.table().select().range().order().execute.return_value = \
                mock_supabase_response([])

            from app.services.telemetria_service import list_telemetry, MAX_LIMIT
            list_telemetry(limit=99999)

            # Verificar que range se llamó con MAX_LIMIT como techo
            call_args = mock_sb.table().select().range.call_args
            assert call_args[0][1] <= MAX_LIMIT


# ── Tests de validación Pydantic ──────────────────

class TestTelemetriaInputValidacion:

    def test_humedad_fuera_de_rango(self):
        """Rechaza humedad > 100."""
        with pytest.raises(Exception):
            TelemetriaInput(humedad=150.0, sensor_id=SENSOR_ID)

    def test_ph_fuera_de_rango(self):
        """Rechaza ph > 14."""
        with pytest.raises(Exception):
            TelemetriaInput(ph=20.0, sensor_id=SENSOR_ID)

    def test_todos_campos_none(self):
        """Rechaza input sin ningún campo de medición."""
        with pytest.raises(Exception):
            TelemetriaInput(sensor_id=SENSOR_ID)

    def test_un_campo_es_suficiente(self):
        """Acepta input con al menos un campo."""
        data = TelemetriaInput(humedad=50.0, sensor_id=SENSOR_ID)
        assert data.humedad == 50.0