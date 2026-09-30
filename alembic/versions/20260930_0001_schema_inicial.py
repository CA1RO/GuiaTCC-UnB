"""Schema inicial da fonte OLTP e dos módulos da aplicação.

Revision ID: 20260930_0001
Revises:
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


revision: str = "20260930_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")

    op.create_table(
        "departamento",
        sa.Column("id_departamento", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("sigla", sa.String(20)),
        sa.Column("faculdade", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("nome", name="uq_departamento_nome"),
    )
    op.create_index("idx_departamento_nome", "departamento", ["nome"])

    op.create_table(
        "docente",
        sa.Column("id_docente", sa.Integer(), primary_key=True),
        sa.Column("id_capes", sa.Integer()),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column("email", sa.String(200)),
        sa.Column("titulacao", sa.String(100)),
        sa.Column("ano_titulacao", sa.Integer()),
        sa.Column("area_titulacao", sa.String(200)),
        sa.Column("tipo_vinculo", sa.String(100)),
        sa.Column("regime_trabalho", sa.String(100)),
        sa.Column("link_lattes", sa.String(500)),
        sa.Column("id_lattes", sa.String(50)),
        sa.Column("id_departamento", sa.Integer()),
        sa.Column("situacao", sa.String(50), server_default="ativo", nullable=False),
        sa.Column("data_atualizacao", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["id_departamento"], ["departamento.id_departamento"]),
        sa.UniqueConstraint("id_capes", name="uq_docente_id_capes"),
        sa.UniqueConstraint("id_lattes", name="uq_docente_id_lattes"),
    )
    op.create_index("idx_docente_nome", "docente", ["nome"])
    op.create_index("idx_docente_departamento", "docente", ["id_departamento"])
    op.execute("CREATE INDEX idx_docente_nome_trgm ON docente USING gin (nome gin_trgm_ops)")

    op.create_table(
        "programa_pos_graduacao",
        sa.Column("id_programa", sa.Integer(), primary_key=True),
        sa.Column("codigo_capes", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column("grau", sa.String(80)),
        sa.Column("modalidade", sa.String(80)),
        sa.Column("conceito", sa.String(10)),
        sa.Column("area_avaliacao", sa.String(200)),
        sa.Column("grande_area_conhecimento", sa.String(200)),
        sa.Column("area_conhecimento", sa.String(200)),
        sa.Column("municipio", sa.String(150)),
        sa.Column("uf", sa.String(2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("codigo_capes", name="uq_programa_codigo_capes"),
    )
    op.create_index("idx_programa_area", "programa_pos_graduacao", ["area_avaliacao"])

    op.create_table(
        "docente_programa",
        sa.Column("id_docente", sa.Integer(), nullable=False),
        sa.Column("id_programa", sa.Integer(), nullable=False),
        sa.Column("ano_base", sa.Integer(), nullable=False),
        sa.Column("categoria_docente", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["id_docente"], ["docente.id_docente"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["id_programa"],
            ["programa_pos_graduacao.id_programa"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id_docente", "id_programa", "ano_base"),
    )
    op.create_index("idx_docente_programa_programa", "docente_programa", ["id_programa"])
    op.create_index("idx_docente_programa_ano", "docente_programa", ["ano_base"])

    op.create_table(
        "projeto_pesquisa",
        sa.Column("id_projeto", sa.Integer(), primary_key=True),
        sa.Column("id_docente", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(500), nullable=False),
        sa.Column("descricao", sa.Text()),
        sa.Column("ano_inicio", sa.Integer()),
        sa.Column("ano_fim", sa.Integer()),
        sa.Column("status", sa.String(50), server_default="ativo", nullable=False),
        sa.Column("palavras_chave", postgresql.ARRAY(sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "ano_fim IS NULL OR ano_inicio IS NULL OR ano_fim >= ano_inicio",
            name="ck_projeto_intervalo_anos",
        ),
        sa.ForeignKeyConstraint(["id_docente"], ["docente.id_docente"], ondelete="CASCADE"),
    )
    op.create_index("idx_projeto_docente", "projeto_pesquisa", ["id_docente"])
    op.create_index("idx_projeto_status", "projeto_pesquisa", ["status"])
    op.create_index("idx_projeto_anos", "projeto_pesquisa", ["ano_inicio", "ano_fim"])

    op.create_table(
        "chunk_vetorial",
        sa.Column("id_chunk", sa.Integer(), primary_key=True),
        sa.Column("id_docente", sa.Integer(), nullable=False),
        sa.Column("id_projeto", sa.Integer()),
        sa.Column("conteudo_texto", sa.Text(), nullable=False),
        sa.Column("embedding_vetor", Vector(1536)),
        sa.Column("metadados_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["id_docente"], ["docente.id_docente"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["id_projeto"], ["projeto_pesquisa.id_projeto"], ondelete="SET NULL"),
    )
    op.create_index("idx_chunk_docente", "chunk_vetorial", ["id_docente"])
    op.create_index("idx_chunk_projeto", "chunk_vetorial", ["id_projeto"])
    op.create_index("idx_chunk_metadados", "chunk_vetorial", ["metadados_json"], postgresql_using="gin")
    op.execute(
        "CREATE INDEX idx_chunk_embedding_hnsw ON chunk_vetorial "
        "USING hnsw (embedding_vetor vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200)"
    )

    op.create_table(
        "estudante",
        sa.Column("id_estudante", sa.Integer(), primary_key=True),
        sa.Column("matricula", sa.String(20)),
        sa.Column("nome", sa.String(300), nullable=False),
        sa.Column("curso", sa.String(200)),
        sa.Column("areas_interesse", postgresql.ARRAY(sa.Text())),
        sa.Column("tema_pretendido", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("matricula", name="uq_estudante_matricula"),
    )

    op.create_table(
        "sessao_interacao",
        sa.Column("id_sessao", sa.Integer(), primary_key=True),
        sa.Column("id_estudante", sa.Integer()),
        sa.Column("prompt_pergunta", sa.Text(), nullable=False),
        sa.Column("resposta_rag", sa.Text()),
        sa.Column("docentes_sugeridos", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("feedback_nota", sa.SmallInteger()),
        sa.Column("data_hora", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("metadados", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("feedback_nota BETWEEN 1 AND 5", name="ck_sessao_feedback_nota"),
        sa.ForeignKeyConstraint(["id_estudante"], ["estudante.id_estudante"], ondelete="SET NULL"),
    )
    op.create_index("idx_sessao_estudante", "sessao_interacao", ["id_estudante"])
    op.create_index("idx_sessao_data", "sessao_interacao", ["data_hora"])

    op.execute(
        """
        CREATE FUNCTION trigger_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for tabela in (
        "departamento",
        "docente",
        "programa_pos_graduacao",
        "docente_programa",
        "projeto_pesquisa",
        "estudante",
    ):
        op.execute(
            f"CREATE TRIGGER set_updated_at_{tabela} "
            f"BEFORE UPDATE ON {tabela} FOR EACH ROW "
            "EXECUTE FUNCTION trigger_set_updated_at()"
        )


def downgrade() -> None:
    for tabela in (
        "estudante",
        "projeto_pesquisa",
        "docente_programa",
        "programa_pos_graduacao",
        "docente",
        "departamento",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS set_updated_at_{tabela} ON {tabela}")
    op.execute("DROP FUNCTION IF EXISTS trigger_set_updated_at")

    op.drop_table("sessao_interacao")
    op.drop_table("estudante")
    op.drop_table("chunk_vetorial")
    op.drop_table("projeto_pesquisa")
    op.drop_table("docente_programa")
    op.drop_table("programa_pos_graduacao")
    op.drop_table("docente")
    op.drop_table("departamento")
