"""catálogo con slug, disponibilidad y referencia; tiendas con afiliación y feed; clics sin
recomendación

Revision ID: 0003_catalogo_afiliacion
Revises: 0002_secundarias_staging
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_catalogo_afiliacion"
down_revision: str | None = "0002_secundarias_staging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Modelo: nombre comercial y slug de la ficha.
    op.add_column("modelo", sa.Column("nombre", sa.String(length=200), nullable=False))
    op.add_column("modelo", sa.Column("slug", sa.String(length=200), nullable=False))
    op.create_unique_constraint(op.f("uq_modelo_slug"), "modelo", ["slug"])

    # Tienda: enlace de afiliado y feed de productos.
    op.add_column("tienda", sa.Column("plantilla_enlace", sa.String(length=2048), nullable=True))
    op.add_column("tienda", sa.Column("id_afiliado", sa.String(length=100), nullable=True))
    op.add_column("tienda", sa.Column("feed_url", sa.String(length=2048), nullable=True))
    op.add_column("tienda", sa.Column("feed_formato", sa.String(length=10), nullable=True))
    op.add_column(
        "tienda",
        sa.Column(
            "feed_campos",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )

    # Oferta: disponibilidad con tres valores (sustituye a disponible) y referencia del feed.
    op.add_column(
        "oferta",
        sa.Column("disponibilidad", sa.String(length=20), server_default="stock", nullable=False),
    )
    op.execute("UPDATE oferta SET disponibilidad = 'agotada' WHERE NOT disponible")
    op.drop_column("oferta", "disponible")
    op.add_column("oferta", sa.Column("referencia", sa.String(length=200), nullable=True))
    op.create_unique_constraint(op.f("uq_oferta_tienda_id"), "oferta", ["tienda_id", "referencia"])

    # Clic: también desde la ficha o el catálogo, sin recomendación.
    op.alter_column("rec_click", "recomendacion_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("rec_click", "posicion", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "rec_click",
        sa.Column("origen", sa.String(length=20), server_default="recomendacion", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("rec_click", "origen")
    op.execute("DELETE FROM rec_click WHERE recomendacion_id IS NULL OR posicion IS NULL")
    op.alter_column("rec_click", "posicion", existing_type=sa.Integer(), nullable=False)
    op.alter_column("rec_click", "recomendacion_id", existing_type=sa.Integer(), nullable=False)

    op.drop_constraint(op.f("uq_oferta_tienda_id"), "oferta", type_="unique")
    op.drop_column("oferta", "referencia")
    op.add_column(
        "oferta",
        sa.Column("disponible", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.execute("UPDATE oferta SET disponible = (disponibilidad <> 'agotada')")
    op.alter_column("oferta", "disponible", server_default=None)
    op.drop_column("oferta", "disponibilidad")

    op.drop_column("tienda", "feed_campos")
    op.drop_column("tienda", "feed_formato")
    op.drop_column("tienda", "feed_url")
    op.drop_column("tienda", "id_afiliado")
    op.drop_column("tienda", "plantilla_enlace")

    op.drop_constraint(op.f("uq_modelo_slug"), "modelo", type_="unique")
    op.drop_column("modelo", "slug")
    op.drop_column("modelo", "nombre")
