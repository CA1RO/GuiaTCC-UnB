"""Carimbo de evento do docente e nome único para a carga da origem.

Revision ID: 0002_docente_origem
Revises:
Create Date: 2026-09-28
"""

from pathlib import Path

from alembic import op

revision = "0002_docente_origem"
down_revision = None
branch_labels = None
depends_on = None

SQL = (
    Path(__file__).resolve().parents[2] / "db" / "migrations" / "0002_docente_origem.sql"
)


def upgrade() -> None:
    for comando in SQL.read_text(encoding="utf-8").split(";"):
        if comando.strip():
            op.execute(comando)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_docente_nome")
    op.execute("ALTER TABLE docente DROP COLUMN IF EXISTS data_lotacao")
    op.execute("ALTER TABLE docente DROP COLUMN IF EXISTS data_ingresso_orgao")
