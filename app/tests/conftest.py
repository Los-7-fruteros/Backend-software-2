import pytest
import uuid
from unittest.mock import MagicMock
from app.models.umbrales_model import UmbralInput
from app.models.telemetria_model import TelemetriaInput 



# ── UUIDs fijos para todos los tests ──────────────
SENSOR_ID  = uuid.uuid4()
PREDIO_ID  = uuid.uuid4()
ALERTA_ID  = uuid.uuid4()
UMBRAL_ID  = uuid.uuid4()


# ── Fixtures de datos base ─────────────────────────

@pytest.fixture
def sensor_data():
    return {
        "id":        str(SENSOR_ID),
        "predio_id": str(PREDIO_ID),
        "sector":    "sector-1",
        "device_id": "DEV-001"
    }

@pytest.fixture
def telemetria_data():
    return {
        "id":          str(uuid.uuid4()),
        "sensor_id":   str(SENSOR_ID),
        "humedad":     65.0,
        "temperatura": 22.0,
        "ph":          7.0,
        "voltaje":     12.0,
        "created_at":  "2024-01-01T00:00:00"
    }

@pytest.fixture
def alerta_data():
    return {
        "id":        str(ALERTA_ID),
        "sensor_id": str(SENSOR_ID),
        "tipo":      "humedad",
        "valor":     95.0,
        "mensaje":   "Humedad por encima del máximo: 95.0 > 90.0",
        "created_at": "2024-01-01T00:00:00"
    }

@pytest.fixture
def umbrales_data():
    return {
        "id":              str(UMBRAL_ID),
        "predio_id":       str(PREDIO_ID),
        "humedad_min":     30.0,
        "humedad_max":     90.0,
        "temperatura_min": 10.0,
        "temperatura_max": 40.0,
        "ph_min":          5.5,
        "ph_max":          8.5,
        "voltaje_min":     10.0,
        "created_at":      "2024-01-01T00:00:00"
    }

@pytest.fixture
def mock_supabase_response():
    """Factory para simular respuestas de Supabase."""
    def _make(data: list):
        mock = MagicMock()
        mock.data = data
        return mock
    return _make