"""fallos de enlace de cada oferta y ficha propuesta por la IA para las palas nuevas

Revision ID: 0004_enlaces_y_fichas
Revises: 0003_catalogo_afiliacion
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_enlaces_y_fichas"
down_revision: str | None = "0003_catalogo_afiliacion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "oferta",
        sa.Column("enlace_fallos", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "revision_pendiente",
        sa.Column("propuesta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="staging",
    )


def downgrade() -> None:
    op.drop_column("revision_pendiente", "propuesta", schema="staging")
    op.drop_column("oferta", "enlace_fallos")
