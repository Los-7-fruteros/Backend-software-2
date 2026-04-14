from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alertas import router as alertas_router
from app.api.predio import router as predios_router
from app.api.sensores import router as sensores_router
from app.api.telemetry import router as telemetry_router
from app.api.umbrales import router as umbrales_router
from app.api.usuario import auth_router, router as usuarios_router
from app.utils.middlewares import (          # ← nuevo
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 API iniciada")
    yield
    print("🛑 API detenida")


app = FastAPI(
    title="API Monitoreo Agrícola IoT",
    description="Backend para monitoreo de sensores en predios agrícolas",
    version="2.0.0",                         # ← Sprint 2
    lifespan=lifespan,
)

# ── Middlewares ────────────────────────────────────────
# IMPORTANTE: se ejecutan en orden inverso al que se agregan
app.add_middleware(RequestLoggingMiddleware)     # 4° — trazabilidad de requests
app.add_middleware(SecurityHeadersMiddleware)    # 3° — headers de seguridad
app.add_middleware(RateLimitMiddleware)          # 2° — protección fuerza bruta/DoS
app.add_middleware(RequestSizeLimitMiddleware)   # 1° — límite tamaño de payload
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://frontend-production-98d34.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────
app.include_router(auth_router)
app.include_router(telemetry_router)
app.include_router(alertas_router)
app.include_router(sensores_router)
app.include_router(predios_router)
app.include_router(umbrales_router)
app.include_router(usuarios_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "api": "Monitoreo Agrícola IoT", "version": "2.0.0"}
