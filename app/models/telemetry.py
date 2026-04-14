from pydantic import BaseModel, Field

class TelemetryInput(BaseModel):
    deveui: str = Field(..., example="ABC123")
    humedad: float
    temperatura: float
    ph: float
    voltaje: float