"""
Etapa 3 do Pipeline — Chunking e Geração de Embeddings Semânticos

Responsável por:
- Divisão de textos em janelas de 512 tokens com overlap de 64
- Geração de embeddings densos (1536d) via OpenAI text-embedding-3-small
- Inserção na tabela chunk_vetorial (PostgreSQL + pgvector HNSW)

Ferramentas: LangChain + OpenAI API + pgvector
Frequência: Semanal (domingos às 06h).
Conforme aba "5 Pipeline", linha 3.
"""

import logging
import re

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.db.models import ChunkVetorial, Docente, ProjetoPesquisa

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "quero", "trabalhar", "com", "alguem", "alguém", "para", "sobre", "quem",
    "pesquisa", "pesquisam", "uma", "uns", "das", "dos", "que", "por", "como",
    "meu", "minha", "tema", "orientador", "orientadora",
}


def chunkar_texto(texto: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Divide texto em janelas de tokens (aproximação por palavras).

    Args:
        texto: Texto original para chunking.
        chunk_size: Tamanho do chunk em tokens (~palavras). Default: 512.
        overlap: Sobreposição entre chunks. Default: 64.

    Returns:
        Lista de chunks de texto.
    """
    chunk_size = chunk_size or settings.rag_chunk_size
    overlap = overlap or settings.rag_chunk_overlap

    palavras = texto.split()
    if len(palavras) <= chunk_size:
        return [texto]

    chunks = []
    inicio = 0
    while inicio < len(palavras):
        fim = inicio + chunk_size
        chunk = " ".join(palavras[inicio:fim])
        chunks.append(chunk)
        inicio += chunk_size - overlap

    return chunks


def get_embedding_model() -> OpenAIEmbeddings:
    """Retorna o modelo de embeddings configurado."""
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )


async def gerar_embeddings_docente(
    db: AsyncSession,
    id_docente: int,
    textos: list[str],
    metadados_base: dict | None = None,
) -> list[ChunkVetorial]:
    """
    Gera embeddings para chunks de texto de um docente e persiste no banco.

    Args:
        db: Sessão do banco de dados.
        id_docente: ID do docente.
        textos: Lista de textos (resumos, projetos, artigos).
        metadados_base: Metadados extras para cada chunk.

    Returns:
        Lista de ChunkVetorial criados.
    """
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY não configurada. Embeddings não gerados.")
        return []

    embedding_model = get_embedding_model()
    chunks_criados = []

    for texto in textos:
        chunks_texto = chunkar_texto(texto)
        embeddings = embedding_model.embed_documents(chunks_texto)

        for chunk_texto, vetor in zip(chunks_texto, embeddings):
            chunk = ChunkVetorial(
                id_docente=id_docente,
                conteudo_texto=chunk_texto,
                embedding_vetor=vetor,
                metadados_json=metadados_base or {},
            )
            db.add(chunk)
            chunks_criados.append(chunk)

    await db.flush()
    logger.info(f"Gerados {len(chunks_criados)} chunks para docente {id_docente}")
    return chunks_criados


async def indexar_projetos_se_vazio(db: AsyncSession) -> int:
    """Gera embeddings dos projetos cadastrados quando a base vetorial ainda está vazia."""
    total = await db.scalar(select(func.count()).select_from(ChunkVetorial))
    if total:
        return 0

    result = await db.execute(
        select(ProjetoPesquisa).options(
            selectinload(ProjetoPesquisa.docente).selectinload(Docente.departamento)
        )
    )
    projetos = result.scalars().all()
    if not projetos:
        return 0

    textos = []
    for projeto in projetos:
        docente = projeto.docente
        departamento = docente.departamento.nome if docente and docente.departamento else ""
        chaves = ", ".join(projeto.palavras_chave or [])
        textos.append(
            f"Docente: {docente.nome}. Departamento: {departamento}. "
            f"Projeto: {projeto.titulo}. {projeto.descricao or ''} Palavras-chave: {chaves}."
        )

    vetores = get_embedding_model().embed_documents(textos)
    for projeto, texto, vetor in zip(projetos, textos, vetores):
        db.add(
            ChunkVetorial(
                id_docente=projeto.id_docente,
                id_projeto=projeto.id_projeto,
                conteudo_texto=texto,
                embedding_vetor=vetor,
                metadados_json={"titulo": projeto.titulo, "id_projeto": projeto.id_projeto},
            )
        )
    await db.flush()
    logger.info("Indexados %s projetos na base vetorial", len(projetos))
    return len(projetos)


async def buscar_lexical(
    db: AsyncSession,
    pergunta: str,
    top_k: int = None,
    filtro_departamento: str | None = None,
) -> list[dict]:
    """Busca por semelhança de texto quando o provedor de embeddings não responde."""
    from src.db.models import Departamento

    top_k = top_k or settings.rag_top_k
    termos = [
        termo
        for termo in re.findall(r"[0-9a-záàâãéêíóôõúç]+", pergunta.lower())
        if len(termo) > 3 and termo not in _STOPWORDS
    ] or [pergunta]

    corpus = func.concat_ws(
        " ",
        ProjetoPesquisa.titulo,
        func.coalesce(ProjetoPesquisa.descricao, ""),
        func.coalesce(func.array_to_string(ProjetoPesquisa.palavras_chave, " "), ""),
        Docente.nome,
    )
    score = func.greatest(*(func.word_similarity(termo, corpus) for termo in termos))
    stmt = (
        select(ProjetoPesquisa, Docente.nome.label("nome_docente"), score.label("similaridade"))
        .join(Docente, ProjetoPesquisa.id_docente == Docente.id_docente)
        .where(score > 0.45)
        .order_by(desc(score))
        .limit(top_k)
    )
    if filtro_departamento:
        stmt = stmt.join(Departamento, Docente.id_departamento == Departamento.id_departamento).where(
            Departamento.nome.ilike(f"%{filtro_departamento}%")
        )

    result = await db.execute(stmt)
    return [
        {
            "id_chunk": row.ProjetoPesquisa.id_projeto,
            "conteudo_texto": f"Projeto: {row.ProjetoPesquisa.titulo}. {row.ProjetoPesquisa.descricao or ''}",
            "nome_docente": row.nome_docente,
            "similaridade": float(row.similaridade),
            "metadados": {"titulo": row.ProjetoPesquisa.titulo, "id_projeto": row.ProjetoPesquisa.id_projeto},
        }
        for row in result.all()
    ]


async def buscar_similar(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = None,
    filtro_departamento: str | None = None,
) -> list[dict]:
    """
    Busca semântica top-k no pgvector usando distância de cosseno (HNSW).

    Args:
        db: Sessão do banco de dados.
        query_embedding: Vetor do prompt do aluno.
        top_k: Número de resultados.
        filtro_departamento: Filtro opcional por departamento.

    Returns:
        Lista de chunks mais similares com score.
    """
    from pgvector.sqlalchemy import Vector
    from sqlalchemy import func

    top_k = top_k or settings.rag_top_k

    stmt = (
        select(
            ChunkVetorial,
            Docente.nome.label("nome_docente"),
            (1 - ChunkVetorial.embedding_vetor.cosine_distance(query_embedding)).label("similaridade"),
        )
        .join(Docente, ChunkVetorial.id_docente == Docente.id_docente)
    )

    if filtro_departamento:
        from src.db.models import Departamento

        stmt = stmt.join(Departamento, Docente.id_departamento == Departamento.id_departamento).where(
            Departamento.nome.ilike(f"%{filtro_departamento}%")
        )

    stmt = stmt.order_by(
        ChunkVetorial.embedding_vetor.cosine_distance(query_embedding)
    ).limit(top_k)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id_chunk": row.ChunkVetorial.id_chunk,
            "conteudo_texto": row.ChunkVetorial.conteudo_texto,
            "nome_docente": row.nome_docente,
            "similaridade": float(row.similaridade),
            "metadados": row.ChunkVetorial.metadados_json,
        }
        for row in rows
    ]
