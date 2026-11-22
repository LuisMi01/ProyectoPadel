"""esquema staging, vocab_map y afiliación (docs/BASE_DE_DATOS.md)

- Crea el esquema staging con importacion, producto_feed y revision_pendiente.
- public.vocab_map: traducción de valores de cada tienda a uno único.
- public.tienda: plantilla_enlace, id_afiliado, parametro_subid.
- public.rec_click: origen; recomendacion_id y posicion pasan a ser opcionales
  (clics desde la ficha o las palas guardadas, sin recomendación).

Revision ID: 0002_esquema_staging
Revises: 0001_inicial
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_esquema_staging"
down_revision: str | None = "0001_inicial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ORIGENES = "'recomendacion', 'ficha', 'palas_guardadas', 'alerta_precio'"


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS staging")

    # --- public.tienda: datos para construir el enlace de afiliado ------------------
    op.add_column("tienda", sa.Column("plantilla_enlace", sa.String(length=2048), nullable=True))
    op.add_column("tienda", sa.Column("id_afiliado", sa.String(length=100), nullable=True))
    op.add_column("tienda", sa.Column("parametro_subid", sa.String(length=50), nullable=True))

    # --- public.rec_click: origen del clic y recomendación opcional -----------------
    op.add_column(
        "rec_click",
        sa.Column("origen", sa.String(length=30), server_default="recomendacion", nullable=False),
    )
    op.create_check_constraint(op.f("ck_rec_click_origen"), "rec_click", f"origen IN ({ORIGENES})")
    op.alter_column("rec_click", "recomendacion_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("rec_click", "posicion", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint(
        op.f("fk_rec_click_recomendacion_id_recomendacion"), "rec_click", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_rec_click_recomendacion_id_recomendacion"),
        "rec_click",
        "recomendacion",
        ["recomendacion_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- public.vocab_map ------------------------------------------------------------
    op.create_table(
        "vocab_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campo", sa.String(length=50), nullable=False),
        sa.Column("valor_origen", sa.String(length=200), nullable=False),
        sa.Column("valor", sa.String(length=100), nullable=False),
        sa.Column("tienda_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tienda_id"],
            ["tienda.id"],
            name=op.f("fk_vocab_map_tienda_id_tienda"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vocab_map")),
        sa.UniqueConstraint(
            "campo",
            "valor_origen",
            "tienda_id",
            name="uq_vocab_map_campo_valor_tienda",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(op.f("ix_vocab_map_tienda_id"), "vocab_map", ["tienda_id"], unique=False)

    # --- staging ---------------------------------------------------------------------
    op.create_table(
        "importacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tienda_id", sa.Integer(), nullable=False),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("productos_recibidos", sa.Integer(), server_default="0", nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="en_curso", nullable=False),
        sa.CheckConstraint(
            "estado IN ('en_curso', 'correcta', 'fallida', 'descartada')",
            name=op.f("ck_importacion_estado"),
        ),
        sa.ForeignKeyConstraint(
            ["tienda_id"],
            ["tienda.id"],
            name=op.f("fk_importacion_tienda_id_tienda"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_importacion")),
        schema="staging",
    )
    op.create_index(
        "ix_importacion_tienda_fecha",
        "importacion",
        ["tienda_id", "fecha"],
        unique=False,
        schema="staging",
    )

    op.create_table(
        "producto_feed",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("importacion_id", sa.Integer(), nullable=False),
        sa.Column("sku_id", sa.Integer(), nullable=True),
        sa.Column("datos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["importacion_id"],
            ["staging.importacion.id"],
            name=op.f("fk_producto_feed_importacion_id_importacion"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["sku_id"],
            ["sku.id"],
            name=op.f("fk_producto_feed_sku_id_sku"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_producto_feed")),
        schema="staging",
    )
    op.create_index(
        op.f("ix_staging_producto_feed_importacion_id"),
        "producto_feed",
        ["importacion_id"],
        unique=False,
        schema="staging",
    )
    op.create_index(
        op.f("ix_staging_producto_feed_sku_id"),
        "producto_feed",
        ["sku_id"],
        unique=False,
        schema="staging",
    )

    op.create_table(
        "revision_pendiente",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("producto_feed_id", sa.BigInteger(), nullable=False),
        sa.Column("motivo", sa.String(length=30), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="pendiente", nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'aprobado', 'rechazado')",
            name=op.f("ck_revision_pendiente_estado"),
        ),
        sa.CheckConstraint(
            "motivo IN ('emparejamiento_dudoso', 'pala_nueva', 'precio_anomalo')",
            name=op.f("ck_revision_pendiente_motivo"),
        ),
        sa.ForeignKeyConstraint(
            ["producto_feed_id"],
            ["staging.producto_feed.id"],
            name=op.f("fk_revision_pendiente_producto_feed_id_producto_feed"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revision_pendiente")),
        schema="staging",
    )
    op.create_index(
        op.f("ix_staging_revision_pendiente_producto_feed_id"),
        "revision_pendiente",
        ["producto_feed_id"],
        unique=False,
        schema="staging",
    )
    op.create_index(
        "ix_revision_pendiente_cola",
        "revision_pendiente",
        ["creado_en"],
        unique=False,
        schema="staging",
        postgresql_where=sa.text("estado = 'pendiente'"),
    )


def downgrade() -> None:
    op.drop_table("revision_pendiente", schema="staging")
    op.drop_table("producto_feed", schema="staging")
    op.drop_table("importacion", schema="staging")
    op.execute("DROP SCHEMA IF EXISTS staging")

    op.drop_table("vocab_map")

    # Antes de 0002 todo clic tenía recomendación y posición: los que no la tienen
    # no caben en el esquema anterior y se pierden al bajar.
    op.execute("DELETE FROM rec_click WHERE recomendacion_id IS NULL OR posicion IS NULL")
    op.drop_constraint(
        op.f("fk_rec_click_recomendacion_id_recomendacion"), "rec_click", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_rec_click_recomendacion_id_recomendacion"),
        "rec_click",
        "recomendacion",
        ["recomendacion_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("rec_click", "posicion", existing_type=sa.Integer(), nullable=False)
    op.alter_column("rec_click", "recomendacion_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint(op.f("ck_rec_click_origen"), "rec_click", type_="check")
    op.drop_column("rec_click", "origen")

    op.drop_column("tienda", "parametro_subid")
    op.drop_column("tienda", "id_afiliado")
    op.drop_column("tienda", "plantilla_enlace")
