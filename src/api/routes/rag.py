"""Endpoint de busca semântica (RAG) — interface do chat interativo."""

import logging

from fastapi import APIRouter, Depends
from openai import APIStatusError, OpenAI, RateLimitError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import SessaoInteracao
from src.db.session import get_db
from src.pipeline.embeddings import (
    buscar_lexical,
    buscar_similar,
    get_embedding_model,
    indexar_projetos_se_vazio,
)

logger = logging.getLogger(__name__)

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


def _responder(pergunta: str, chunks: list[dict]) -> str:
    contexto = "\n\n".join(
        f"- {chunk['nome_docente']}: {chunk['conteudo_texto']}" for chunk in chunks
    )
    cliente = OpenAI(api_key=settings.openai_api_key)
    resposta = cliente.chat.completions.create(
        model=settings.openai_llm_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você ajuda alunos da UnB a escolher orientador de TCC. "
                    "Use somente os trechos fornecidos. Responda em português, "
                    "cite o nome do docente e o projeto, e diga por que o tema se aproxima. "
                    "Se nenhum trecho servir, diga isso com clareza."
                ),
            },
            {
                "role": "user",
                "content": f"Pergunta do aluno: {pergunta}\n\nTrechos recuperados:\n{contexto}",
            },
        ],
    )
    return resposta.choices[0].message.content or ""


def _resposta_textual(pergunta: str, chunks: list[dict]) -> str:
    principais = chunks[:3]
    indicacoes = " ".join(
        f"{chunk['nome_docente']} conduz “{chunk['metadados'].get('titulo', 'um projeto relacionado')}”."
        for chunk in principais
    )
    return (
        "A chave da OpenAI foi reconhecida, mas a conta está sem créditos, "
        "então a recomendação saiu da busca textual dos projetos cadastrados. "
        f"Para “{pergunta}”, {indicacoes}"
    )


def _registrar(db: AsyncSession, payload: PerguntaRequest, resposta: str, chunks: list[dict]) -> None:
    db.add(
        SessaoInteracao(
            id_estudante=payload.id_estudante,
            prompt_pergunta=payload.pergunta,
            resposta_rag=resposta,
            docentes_sugeridos=[
                {"nome": chunk["nome_docente"], "id_chunk": chunk["id_chunk"]} for chunk in chunks
            ],
        )
    )


@router.post("/buscar", response_model=PerguntaResponse)
async def buscar_orientador(
    payload: PerguntaRequest,
    db: AsyncSession = Depends(get_db),
):
    """Gera o embedding da pergunta, busca os trechos mais próximos e redige a recomendação."""
    if not settings.openai_api_key:
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[],
            resposta_rag=None,
            mensagem=(
                "A chave da OpenAI não chegou na API. "
                "Salve OPENAI_API_KEY no .env e reinicie o container: docker compose up -d"
            ),
        )

    try:
        await indexar_projetos_se_vazio(db)
        vetor = get_embedding_model().embed_query(payload.pergunta)
        encontrados = await buscar_similar(
            db,
            vetor,
            top_k=payload.top_k,
            filtro_departamento=payload.departamento,
        )
    except RateLimitError:
        logger.warning("OpenAI sem créditos; usando busca textual")
        encontrados = await buscar_lexical(
            db,
            payload.pergunta,
            top_k=payload.top_k,
            filtro_departamento=payload.departamento,
        )
        if not encontrados:
            return PerguntaResponse(
                pergunta=payload.pergunta,
                chunks_relevantes=[],
                resposta_rag=None,
                mensagem=(
                    "A chave da OpenAI foi reconhecida, mas a conta está sem créditos "
                    "e a busca textual não achou um projeto próximo."
                ),
            )
        resposta = _resposta_textual(payload.pergunta, encontrados)
        _registrar(db, payload, resposta, encontrados)
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[ChunkResult(**chunk) for chunk in encontrados],
            resposta_rag=resposta,
            mensagem="Recomendação textual, porque a conta OpenAI está sem créditos.",
        )
    except APIStatusError as exc:
        logger.warning("OpenAI recusou a chamada com status %s", exc.status_code)
        mensagem = (
            "A OpenAI recusou a chave. Gere outra em platform.openai.com e atualize o .env."
            if exc.status_code in {401, 403}
            else "A OpenAI não completou a busca semântica agora."
        )
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[],
            resposta_rag=None,
            mensagem=mensagem,
        )
    except Exception:
        logger.exception("Falha ao consultar embeddings")
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[],
            resposta_rag=None,
            mensagem="Não foi possível gerar a busca semântica. Tente de novo em instantes.",
        )

    if not encontrados:
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[],
            resposta_rag=None,
            mensagem="Nenhum projeto cadastrado se aproxima dessa pergunta.",
        )

    try:
        resposta = _responder(payload.pergunta, encontrados)
    except Exception:
        logger.exception("Falha ao gerar a resposta do modelo")
        return PerguntaResponse(
            pergunta=payload.pergunta,
            chunks_relevantes=[ChunkResult(**chunk) for chunk in encontrados],
            resposta_rag=None,
            mensagem="A busca encontrou docentes, mas a redação da resposta falhou.",
        )

    _registrar(db, payload, resposta, encontrados)
    return PerguntaResponse(
        pergunta=payload.pergunta,
        chunks_relevantes=[ChunkResult(**chunk) for chunk in encontrados],
        resposta_rag=resposta,
        mensagem="Recomendação gerada a partir dos projetos cadastrados.",
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
