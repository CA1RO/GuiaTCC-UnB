"""Modelos SQLAlchemy — mapeamento ORM das entidades do GuiaOrientador-UnB."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Departamento(Base):
    __tablename__ = "departamento"

    id_departamento: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    sigla: Mapped[str | None] = mapped_column(String(20))
    faculdade: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    docentes: Mapped[list["Docente"]] = relationship(back_populates="departamento")


class Docente(Base):
    __tablename__ = "docente"

    id_docente: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_capes: Mapped[int | None] = mapped_column(Integer, unique=True)
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200))
    titulacao: Mapped[str | None] = mapped_column(String(100))
    ano_titulacao: Mapped[int | None] = mapped_column(Integer)
    area_titulacao: Mapped[str | None] = mapped_column(String(200))
    tipo_vinculo: Mapped[str | None] = mapped_column(String(100))
    regime_trabalho: Mapped[str | None] = mapped_column(String(100))
    link_lattes: Mapped[str | None] = mapped_column(String(500))
    id_lattes: Mapped[str | None] = mapped_column(String(50), unique=True)
    id_departamento: Mapped[int | None] = mapped_column(ForeignKey("departamento.id_departamento"))
    situacao: Mapped[str] = mapped_column(String(50), default="ativo")
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    departamento: Mapped["Departamento | None"] = relationship(back_populates="docentes")
    projetos: Mapped[list["ProjetoPesquisa"]] = relationship(back_populates="docente")
    chunks: Mapped[list["ChunkVetorial"]] = relationship(back_populates="docente")
    vinculos_programas: Mapped[list["DocentePrograma"]] = relationship(
        back_populates="docente",
        cascade="all, delete-orphan",
    )


class ProgramaPosGraduacao(Base):
    __tablename__ = "programa_pos_graduacao"

    id_programa: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_capes: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    grau: Mapped[str | None] = mapped_column(String(80))
    modalidade: Mapped[str | None] = mapped_column(String(80))
    conceito: Mapped[str | None] = mapped_column(String(10))
    area_avaliacao: Mapped[str | None] = mapped_column(String(200))
    grande_area_conhecimento: Mapped[str | None] = mapped_column(String(200))
    area_conhecimento: Mapped[str | None] = mapped_column(String(200))
    municipio: Mapped[str | None] = mapped_column(String(150))
    uf: Mapped[str | None] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    vinculos_docentes: Mapped[list["DocentePrograma"]] = relationship(
        back_populates="programa",
        cascade="all, delete-orphan",
    )


class DocentePrograma(Base):
    __tablename__ = "docente_programa"

    id_docente: Mapped[int] = mapped_column(
        ForeignKey("docente.id_docente", ondelete="CASCADE"),
        primary_key=True,
    )
    id_programa: Mapped[int] = mapped_column(
        ForeignKey("programa_pos_graduacao.id_programa", ondelete="CASCADE"),
        primary_key=True,
    )
    ano_base: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_docente: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    docente: Mapped["Docente"] = relationship(back_populates="vinculos_programas")
    programa: Mapped["ProgramaPosGraduacao"] = relationship(back_populates="vinculos_docentes")


class ProjetoPesquisa(Base):
    __tablename__ = "projeto_pesquisa"

    id_projeto: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_docente: Mapped[int] = mapped_column(ForeignKey("docente.id_docente", ondelete="CASCADE"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ano_inicio: Mapped[int | None] = mapped_column(Integer)
    ano_fim: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="ativo")
    palavras_chave: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    docente: Mapped["Docente"] = relationship(back_populates="projetos")
    chunks: Mapped[list["ChunkVetorial"]] = relationship(back_populates="projeto")


class ChunkVetorial(Base):
    __tablename__ = "chunk_vetorial"

    id_chunk: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_docente: Mapped[int] = mapped_column(ForeignKey("docente.id_docente", ondelete="CASCADE"), nullable=False)
    id_projeto: Mapped[int | None] = mapped_column(ForeignKey("projeto_pesquisa.id_projeto", ondelete="SET NULL"))
    conteudo_texto: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_vetor = mapped_column(Vector(1536))
    metadados_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    docente: Mapped["Docente"] = relationship(back_populates="chunks")
    projeto: Mapped["ProjetoPesquisa | None"] = relationship(back_populates="chunks")


class Estudante(Base):
    __tablename__ = "estudante"

    id_estudante: Mapped[int] = mapped_column(Integer, primary_key=True)
    matricula: Mapped[str | None] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    curso: Mapped[str | None] = mapped_column(String(200))
    areas_interesse: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    tema_pretendido: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sessoes: Mapped[list["SessaoInteracao"]] = relationship(back_populates="estudante")


class SessaoInteracao(Base):
    __tablename__ = "sessao_interacao"

    id_sessao: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_estudante: Mapped[int | None] = mapped_column(ForeignKey("estudante.id_estudante", ondelete="SET NULL"))
    prompt_pergunta: Mapped[str] = mapped_column(Text, nullable=False)
    resposta_rag: Mapped[str | None] = mapped_column(Text)
    docentes_sugeridos: Mapped[dict] = mapped_column(JSONB, default=list)
    feedback_nota: Mapped[int | None] = mapped_column(
        SmallInteger,
        CheckConstraint("feedback_nota BETWEEN 1 AND 5"),
    )
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadados: Mapped[dict] = mapped_column(JSONB, default=dict)

    estudante: Mapped["Estudante | None"] = relationship(back_populates="sessoes")
