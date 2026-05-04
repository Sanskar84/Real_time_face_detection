from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing to do — Postgres is initialised by init.sql
    yield
    # Shutdown: close all pooled connections cleanly
    await engine.dispose()


app = FastAPI(
    title="Face Detection API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
async def health():
    """Quick liveness probe — returns 200 when the server is up."""
    return {"status": "ok"}
