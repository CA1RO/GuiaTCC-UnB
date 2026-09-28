"""Endpoint de busca semântica (RAG) — interface do chat interativo."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import ChunkVetorial, Docente, SessaoInteracao
from src.db.session import get_db

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


class PerguntaRequest(BaseModel):
    pergunta: str
    id_estudante: int | None = None
    departamento: str | None = None
    top_k: int = 5


class ChunkResult(BaseModel):
    id_chunk: int
    conteudo_texto: str
    nome_docente: str
    similaridade: float
    metadados: dict

    model_config = {"from_attributes": True}


class PerguntaResponse(BaseModel):
    pergunta: str
    chunks_relevantes: list[ChunkResult]
    resposta_rag: str | None = None
    mensagem: str


@router.post("/buscar", response_model=PerguntaResponse)
async def buscar_orientador(
    payload: PerguntaRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Busca semântica por orientadores.

    Fluxo:
    1. Gera embedding do prompt do aluno via OpenAI.
    2. Busca top-k vizinhos mais próximos (HNSW / cosseno) no pgvector.
    3. (Futuro) Injeta contexto no LLM para gerar resposta RAG.
    """
    # TODO: Integrar com OpenAI para gerar embedding do prompt
    # Por enquanto, retorna placeholder indicando que o pipeline está pronto

    return PerguntaResponse(
        pergunta=payload.pergunta,
        chunks_relevantes=[],
        resposta_rag=None,
        mensagem=(
            "Pipeline RAG configurado. "
            "Configure OPENAI_API_KEY no .env para ativar a busca semântica."
        ),
    )


@router.post("/feedback")
async def registrar_feedback(
    id_sessao: int,
    nota: int,
    db: AsyncSession = Depends(get_db),
):
    """Registra feedback do aluno sobre a recomendação."""
    result = await db.execute(
        select(SessaoInteracao).where(SessaoInteracao.id_sessao == id_sessao)
    )
    sessao = result.scalar_one_or_none()
    if not sessao:
        return {"erro": "Sessão não encontrada"}
    sessao.feedback_nota = nota
    return {"mensagem": "Feedback registrado com sucesso"}
