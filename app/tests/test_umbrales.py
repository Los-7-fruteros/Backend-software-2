import pytest
import uuid
from unittest.mock import patch
from fastapi import HTTPException
from app.models.umbrales_model import UmbralInput
from app.models.telemetria_model import TelemetriaInput 
from conftest import SENSOR_ID, PREDIO_ID, UMBRAL_ID


# ── Helpers ───────────────────────────────────────

def make_input(**kwargs):
    base = {
        "humedad_min": 30.0, "humedad_max": 90.0,
        "temperatura_min": 10.0, "temperatura_max": 40.0,
        "ph_min": 5.5, "ph_max": 8.5,
        "voltaje_min": 10.0,
        "predio_id": PREDIO_ID
    }
    return UmbralInput(**{**base, **kwargs})


# ── Tests de check_umbrales ───────────────────────

class TestCheckUmbrales:

    def test_sin_predio_id(self, mock_supabase_response):
        """No genera alertas si el sensor no tiene predio."""
        from app.services.umbrales_service import check_umbrales
        from app.models.telemetria_model import TelemetriaInput

        sensor = {"id": str(SENSOR_ID), "predio_id": None}
        data   = TelemetriaInput(humedad=95.0, sensor_id=SENSOR_ID)

        result = check_umbrales(sensor, data)
        assert result == []

    def test_sin_umbrales_configurados(self, sensor_data):
        """No genera alertas si el predio no tiene umbrales."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=None):
            from app.services.umbrales_service import check_umbrales
            from app.models.telemetria_model import TelemetriaInput

            data   = TelemetriaInput(humedad=95.0, sensor_id=SENSOR_ID)
            result = check_umbrales(sensor_data, data)
            assert result == []

    def test_genera_alerta_humedad_alta(self, sensor_data, umbrales_data, alerta_data):
        """Genera alerta cuando humedad supera el máximo."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=umbrales_data), \
             patch("app.services.umbrales_service.create_alerta", return_value=alerta_data):

            from app.services.umbrales_service import check_umbrales
            from app.models.telemetria_model import TelemetriaInput

            data   = TelemetriaInput(humedad=95.0, sensor_id=SENSOR_ID)  # max es 90
            result = check_umbrales(sensor_data, data)

            assert len(result) == 1
            assert result[0]["tipo"] == "humedad"

    def test_no_genera_alerta_valores_normales(self, sensor_data, umbrales_data):
        """No genera alertas cuando todos los valores están en rango."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=umbrales_data), \
             patch("app.services.umbrales_service.create_alerta") as mock_alerta:

            from app.services.umbrales_service import check_umbrales
            from app.models.telemetria_model import TelemetriaInput

            data   = TelemetriaInput(humedad=60.0, temperatura=25.0, ph=7.0, voltaje=12.0, sensor_id=SENSOR_ID)
            result = check_umbrales(sensor_data, data)

            assert result == []
            mock_alerta.assert_not_called()

    def test_genera_multiples_alertas(self, sensor_data, umbrales_data, alerta_data):
        """Genera una alerta por cada variable fuera de rango."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=umbrales_data), \
             patch("app.services.umbrales_service.create_alerta", return_value=alerta_data):

            from app.services.umbrales_service import check_umbrales
            from app.models.telemetria_model import TelemetriaInput

            # humedad alta + ph bajo
            data   = TelemetriaInput(humedad=95.0, ph=2.0, sensor_id=SENSOR_ID)
            result = check_umbrales(sensor_data, data)

            assert len(result) == 2


# ── Tests de CRUD ─────────────────────────────────

class TestCreateUmbral:

    def test_create_exitoso(self, umbrales_data, mock_supabase_response):
        """Crea umbral cuando el predio no tiene uno previo."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=None), \
             patch("app.services.umbrales_service.supabase") as mock_sb:

            mock_sb.table().insert().execute.return_value = mock_supabase_response([umbrales_data])

            from app.services.umbrales_service import create_umbral
            result = create_umbral(make_input())

            assert result["predio_id"] == str(PREDIO_ID)

    def test_create_duplicado(self, umbrales_data):
        """Lanza 409 si el predio ya tiene umbrales."""
        with patch("app.services.umbrales_service.get_umbrales_by_predio", return_value=umbrales_data):
            from app.services.umbrales_service import create_umbral
            with pytest.raises(HTTPException) as exc:
                create_umbral(make_input())
            assert exc.value.status_code == 409


# ── Tests de validación Pydantic ──────────────────

class TestUmbralInputValidacion:

    def test_min_mayor_que_max(self):
        """Rechaza humedad_min >= humedad_max."""
        with pytest.raises(Exception):
            UmbralInput(
                humedad_min=90.0, humedad_max=30.0,  # ← inválido
                temperatura_min=10.0, temperatura_max=40.0,
                ph_min=5.5, ph_max=8.5,
                voltaje_min=10.0,
                predio_id=PREDIO_ID
            )

    def test_rangos_validos(self):
        """Acepta umbrales coherentes."""
        data = make_input()
        assert data.humedad_min < data.humedad_max