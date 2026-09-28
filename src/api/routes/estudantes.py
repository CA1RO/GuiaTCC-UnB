"""Endpoints CRUD para Estudantes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Estudante
from src.db.session import get_db

router = APIRouter(prefix="/api/v1/estudantes", tags=["Estudantes"])


class EstudanteCreate(BaseModel):
    matricula: str | None = None
    nome: str
    curso: str | None = None
    areas_interesse: list[str] | None = None
    tema_pretendido: str | None = None


class EstudanteResponse(BaseModel):
    id_estudante: int
    matricula: str | None
    nome: str
    curso: str | None
    areas_interesse: list[str] | None
    tema_pretendido: str | None

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[EstudanteResponse])
async def listar_estudantes(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Lista estudantes cadastrados."""
    result = await db.execute(select(Estudante).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=EstudanteResponse, status_code=201)
async def criar_estudante(payload: EstudanteCreate, db: AsyncSession = Depends(get_db)):
    """Cadastra um novo estudante."""
    estudante = Estudante(**payload.model_dump())
    db.add(estudante)
    await db.flush()
    await db.refresh(estudante)
    return estudante


@router.get("/{id_estudante}", response_model=EstudanteResponse)
async def obter_estudante(id_estudante: int, db: AsyncSession = Depends(get_db)):
    """Retorna um estudante pelo ID."""
    result = await db.execute(select(Estudante).where(Estudante.id_estudante == id_estudante))
    estudante = result.scalar_one_or_none()
    if not estudante:
        raise HTTPException(status_code=404, detail="Estudante não encontrado")
    return estudante
