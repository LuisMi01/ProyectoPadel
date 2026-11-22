"""token_acceso.ip_hash para limitar los enlaces pedidos desde una misma IP

Revision ID: 0003_token_acceso_ip
Revises: 0002_esquema_staging
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_token_acceso_ip"
down_revision: str | None = "0002_esquema_staging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("token_acceso", sa.Column("ip_hash", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_token_acceso_ip_hash"), "token_acceso", ["ip_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_token_acceso_ip_hash"), table_name="token_acceso")
    op.drop_column("token_acceso", "ip_hash")
