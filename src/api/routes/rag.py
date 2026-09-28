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
from src.pipeline.afinidade import ROTULOS, buscar_afinidade

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


def _responder(pergunta: str, chunks: list[dict], modo: str) -> str:
    contexto = "\n\n".join(
        f"- {chunk['nome_docente']}: {chunk['conteudo_texto']}" for chunk in chunks
    )
    instrucao = (
        "Há projetos alinhados. Apresente cada projeto, o tipo (pesquisa, extensão ou TCC) e o docente responsável."
        if modo == "projetos"
        else "Não há projeto nessa linha. Apresente os docentes e a linha de pesquisa de cada um."
    )
    cliente = OpenAI(api_key=settings.openai_api_key)
    resposta = cliente.chat.completions.create(
        model=settings.openai_llm_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você ajuda alunos da UnB a achar um projeto de pesquisa, extensão ou TCC. "
                    "Use somente o contexto. Responda em português. " + instrucao
                ),
            },
            {"role": "user", "content": f"Afinidade do aluno: {pergunta}\n\nContexto:\n{contexto}"},
        ],
    )
    return resposta.choices[0].message.content or ""


def _resposta_textual(pergunta: str, resultado: dict) -> str:
    if resultado["projetos"]:
        frases = [
            f"{item['nome_docente']} conduz o projeto de {ROTULOS.get(item['tipo'], item['tipo']).lower()} “{item['titulo']}”."
            for item in resultado["projetos"][:3]
        ]
        return f"Há projetos alinhados a “{pergunta}”. " + " ".join(frases)
    if resultado["docentes"]:
        frases = [
            f"{item['nome']} segue esta linha: {item['linha_pesquisa']}."
            for item in resultado["docentes"][:3]
        ]
        return (
            f"Não há projeto de pesquisa, extensão ou TCC alinhado a “{pergunta}”. "
            + " ".join(frases)
        )
    return "Não encontrei projeto nem docente com uma linha próxima desse tema."


def _chunks(resultado: dict) -> list[dict]:
    if resultado["projetos"]:
        return [
            {
                "id_chunk": item["id_projeto"],
                "conteudo_texto": f"{ROTULOS.get(item['tipo'], item['tipo'])}: {item['titulo']}. {item['descricao'] or ''}",
                "nome_docente": item["nome_docente"],
                "similaridade": item["similaridade"] or 0,
                "metadados": {"titulo": item["titulo"], "tipo": item["tipo"]},
            }
            for item in resultado["projetos"]
        ]
    return [
        {
            "id_chunk": item["id_docente"],
            "conteudo_texto": item["linha_pesquisa"] or "",
            "nome_docente": item["nome"],
            "similaridade": item["similaridade"] or 0,
            "metadados": {"linha_pesquisa": item["linha_pesquisa"]},
        }
        for item in resultado["docentes"]
    ]


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
    """Procura projetos alinhados à pergunta. Sem projeto, indica docentes com linha parecida."""
    resultado = await buscar_afinidade(
        db,
        termo=payload.pergunta,
        departamento=payload.departamento,
        limite=payload.top_k,
    )
    encontrados = _chunks(resultado)
    resposta = _resposta_textual(payload.pergunta, resultado)
    if settings.openai_api_key and encontrados:
        try:
            resposta = _responder(payload.pergunta, encontrados, resultado["modo"])
        except (RateLimitError, APIStatusError):
            logger.warning("OpenAI indisponível; a resposta ficou na busca textual")
        except Exception:
            logger.exception("Falha ao redigir a resposta com o modelo")

    if encontrados:
        _registrar(db, payload, resposta, encontrados)
    mensagem = (
        "Projetos alinhados à afinidade informada."
        if resultado["modo"] == "projetos" and resultado["projetos"]
        else "Sem projeto nessa linha; a indicação é pela linha do docente."
        if resultado["docentes"]
        else "Nenhum projeto ou docente se aproxima dessa afinidade."
    )
    return PerguntaResponse(
        pergunta=payload.pergunta,
        chunks_relevantes=[ChunkResult(**chunk) for chunk in encontrados],
        resposta_rag=resposta,
        mensagem=mensagem,
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
