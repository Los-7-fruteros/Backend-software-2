from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alertas import router as alertas_router
from app.api.predio import router as predios_router
from app.api.sensores import router as sensores_router
from app.api.telemetry import router as telemetry_router
from app.api.umbrales import router as umbrales_router
from app.api.usuario import auth_router, router as usuarios_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API iniciada")
    yield
    print("🛑 API detenida")


app = FastAPI(
    title="API Monitoreo Agrícola IoT",
    description="Backend para monitoreo de sensores en predios agrícolas",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(telemetry_router)
app.include_router(alertas_router)
app.include_router(sensores_router)
app.include_router(predios_router)
app.include_router(umbrales_router)
app.include_router(usuarios_router)


@app.get("/")
def root():
    return {"status": "ok"}