"""Ponto de entrada da API FastAPI — GuiaOrientador-UnB."""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import docentes, estudantes, health, rag
from src.config import settings
from src.pipeline.ingestao import garantir_buckets


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
        "API para auxiliar alunos da UnB a encontrar orientadores "
        "e temas de TCC por meio de busca semântica (RAG) sobre "
        "currículos Lattes e dados acadêmicos abertos."
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
app.include_router(docentes.router)
app.include_router(estudantes.router)
app.include_router(rag.router)
