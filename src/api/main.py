"""Ponto de entrada da API FastAPI — GuiaOrientador-UnB."""

from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import busca, docentes, estudantes, health, rag
from src.config import settings
from src.pipeline.ingestao import garantir_buckets

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa e encerra conexões globais."""
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        garantir_buckets()
    except Exception as exc:
        print(f"Aviso: não foi possível criar os buckets do MinIO ({exc})")
    yield
    await app.state.redis.close()


app = FastAPI(
    title="GuiaOrientador-UnB",
    description=(
        "API para o aluno encontrar projetos de pesquisa, extensão ou TCC "
        "alinhados à sua afinidade. Sem projeto, indica docentes com linha parecida."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(docentes.catalogo)
app.include_router(docentes.router)
app.include_router(busca.router)
app.include_router(estudantes.router)
app.include_router(rag.router)


@app.get("/", include_in_schema=False)
async def pagina_inicial():
    """Interface do GuiaOrientador."""
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")
