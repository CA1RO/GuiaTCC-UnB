"""Busca por afinidade do aluno: projetos primeiro, docentes como alternativa."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.pipeline.afinidade import TIPOS, buscar_afinidade

router = APIRouter(prefix="/api/v1/busca", tags=["Busca"])


class ProjetoEncontrado(BaseModel):
    id_projeto: int
    titulo: str
    descricao: str | None
    tipo: str
    status: str
    palavras_chave: list[str] | None
    ano_inicio: int | None
    id_docente: int
    nome_docente: str
    email_docente: str | None
    titulacao: str | None
    departamento_nome: str | None
    departamento_sigla: str | None
    similaridade: float | None


class DocenteEncontrado(BaseModel):
    id_docente: int
    nome: str
    email: str | None
    titulacao: str | None
    linha_pesquisa: str | None
    departamento_nome: str | None
    departamento_sigla: str | None
    similaridade: float | None


class BuscaResponse(BaseModel):
    modo: str
    projetos: list[ProjetoEncontrado]
    docentes: list[DocenteEncontrado]


@router.get("/", response_model=BuscaResponse)
async def buscar(
    q: str | None = Query(None, description="Afinidade ou tema do aluno"),
    tipo: str | None = Query(None, description="pesquisa, extensao ou tcc"),
    departamento: str | None = Query(None, description="Nome do departamento"),
    db: AsyncSession = Depends(get_db),
):
    """Lista projetos alinhados. Sem projeto, devolve docentes com linha parecida."""
    if tipo and tipo not in TIPOS:
        tipo = None
    resultado = await buscar_afinidade(db, termo=q or "", tipo=tipo, departamento=departamento)
    return BuscaResponse(**resultado)
