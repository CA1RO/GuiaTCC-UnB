"""Endpoints CRUD para Docentes e Projetos de Pesquisa."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import Departamento, Docente, ProjetoPesquisa
from src.db.session import get_db

router = APIRouter(prefix="/api/v1/docentes", tags=["Docentes"])


# ── Schemas ─────────────────────────────────────────────────
class DocenteCreate(BaseModel):
    nome: str
    email: str | None = None
    titulacao: str | None = None
    link_lattes: str | None = None
    id_lattes: str | None = None
    id_departamento: int | None = None
    situacao: str = "ativo"


class ProjetoCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    ano_inicio: int | None = None
    ano_fim: int | None = None
    status: str = "ativo"
    palavras_chave: list[str] | None = None


class DocenteResponse(BaseModel):
    id_docente: int
    nome: str
    email: str | None
    titulacao: str | None
    link_lattes: str | None
    id_lattes: str | None
    id_departamento: int | None
    situacao: str

    model_config = {"from_attributes": True}


class ProjetoResponse(BaseModel):
    id_projeto: int
    id_docente: int
    titulo: str
    descricao: str | None
    ano_inicio: int | None
    ano_fim: int | None
    status: str
    palavras_chave: list[str] | None

    model_config = {"from_attributes": True}


# ── Rotas ───────────────────────────────────────────────────
@router.get("/", response_model=list[DocenteResponse])
async def listar_docentes(
    departamento: str | None = Query(None, description="Filtrar por nome do departamento"),
    nome: str | None = Query(None, description="Busca parcial por nome"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Lista docentes com filtros opcionais."""
    stmt = select(Docente)
    if departamento:
        stmt = stmt.join(Departamento).where(Departamento.nome.ilike(f"%{departamento}%"))
    if nome:
        stmt = stmt.where(Docente.nome.ilike(f"%{nome}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{id_docente}", response_model=DocenteResponse)
async def obter_docente(id_docente: int, db: AsyncSession = Depends(get_db)):
    """Retorna um docente pelo ID."""
    result = await db.execute(select(Docente).where(Docente.id_docente == id_docente))
    docente = result.scalar_one_or_none()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    return docente


@router.post("/", response_model=DocenteResponse, status_code=201)
async def criar_docente(payload: DocenteCreate, db: AsyncSession = Depends(get_db)):
    """Cria um novo docente."""
    docente = Docente(**payload.model_dump())
    db.add(docente)
    await db.flush()
    await db.refresh(docente)
    return docente


@router.get("/{id_docente}/projetos", response_model=list[ProjetoResponse])
async def listar_projetos(id_docente: int, db: AsyncSession = Depends(get_db)):
    """Lista projetos de pesquisa de um docente."""
    result = await db.execute(
        select(ProjetoPesquisa).where(ProjetoPesquisa.id_docente == id_docente)
    )
    return result.scalars().all()


@router.post("/{id_docente}/projetos", response_model=ProjetoResponse, status_code=201)
async def criar_projeto(id_docente: int, payload: ProjetoCreate, db: AsyncSession = Depends(get_db)):
    """Cria um projeto de pesquisa para um docente."""
    result = await db.execute(select(Docente).where(Docente.id_docente == id_docente))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Docente não encontrado")
    projeto = ProjetoPesquisa(id_docente=id_docente, **payload.model_dump())
    db.add(projeto)
    await db.flush()
    await db.refresh(projeto)
    return projeto
