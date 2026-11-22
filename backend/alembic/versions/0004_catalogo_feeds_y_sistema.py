"""catálogo con slug, feeds de tiendas, ofertas con disponibilidad y tablas de sistema

Lo que trajo main (cambios_alex) encima del esquema de develop:

- Tablas nuevas: events, metrica_diaria, job_run, feedback y explicacion_cache.
- public.modelo: nombre y slug (único) de la ficha.
- public.tienda: feed_url, feed_formato y feed_campos (jobs.daily.import_feed).
- public.oferta: disponibilidad (stock | ultimas | agotada) en lugar de disponible; referencia
  del producto en el feed (única por tienda) y enlace_fallos (jobs.weekly.check_links).
- public.rec_click: orígenes catalogo y cuenta.
- staging.revision_pendiente: propuesta (ficha que propone la IA para una pala nueva).

Revision ID: 0004_catalogo_feeds_y_sistema
Revises: 0003_token_acceso_ip
Create Date: 2026-11-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_catalogo_feeds_y_sistema"
down_revision: str | None = "0003_token_acceso_ip"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ORIGENES_ANTES = "'recomendacion', 'ficha', 'palas_guardadas', 'alerta_precio'"
ORIGENES = "'recomendacion', 'ficha', 'catalogo', 'cuenta', 'palas_guardadas', 'alerta_precio'"


def upgrade() -> None:
    # --- Tablas de sistema y analítica -------------------------------------------------
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("datos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_fecha"), "events", ["fecha"], unique=False)
    op.create_index(op.f("ix_events_tipo"), "events", ["tipo"], unique=False)
    op.create_table(
        "metrica_diaria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("metrica", sa.String(length=50), nullable=False),
        sa.Column("dimension", sa.String(length=100), server_default="", nullable=False),
        sa.Column("valor", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_metrica_diaria")),
        sa.UniqueConstraint("fecha", "metrica", "dimension", name=op.f("uq_metrica_diaria_fecha")),
    )
    op.create_table(
        "job_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tarea", sa.String(length=50), nullable=False),
        sa.Column("periodo", sa.String(length=20), nullable=False),
        sa.Column(
            "inicio", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("resumen", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_run")),
        sa.UniqueConstraint("tarea", "periodo", name=op.f("uq_job_run_tarea")),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recomendacion_id", sa.Integer(), nullable=False),
        sa.Column("puntuacion", sa.SmallInteger(), nullable=False),
        sa.Column("comentario", sa.String(length=1000), nullable=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("puntuacion BETWEEN 1 AND 5", name=op.f("ck_feedback_puntuacion_rango")),
        sa.ForeignKeyConstraint(
            ["recomendacion_id"],
            ["recomendacion.id"],
            name=op.f("fk_feedback_recomendacion_id_recomendacion"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )
    op.create_index(
        op.f("ix_feedback_recomendacion_id"), "feedback", ["recomendacion_id"], unique=False
    )
    op.create_table(
        "explicacion_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=64), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("modelo", sa.String(length=50), nullable=False),
        sa.Column(
            "creada", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_explicacion_cache")),
        sa.UniqueConstraint("clave", name=op.f("uq_explicacion_cache_clave")),
    )

    # --- Modelo: nombre comercial y slug de la ficha ----------------------------------
    # Se añaden vacíos, se rellenan los modelos que ya hubiera y después se exigen.
    op.add_column("modelo", sa.Column("nombre", sa.String(length=200), nullable=True))
    op.add_column("modelo", sa.Column("slug", sa.String(length=200), nullable=True))
    op.execute(
        "UPDATE modelo SET nombre = f.nombre, slug = 'modelo-' || modelo.id "
        "FROM familia_modelo f WHERE f.id = modelo.familia_id"
    )
    op.alter_column("modelo", "nombre", existing_type=sa.String(length=200), nullable=False)
    op.alter_column("modelo", "slug", existing_type=sa.String(length=200), nullable=False)
    op.create_unique_constraint(op.f("uq_modelo_slug"), "modelo", ["slug"])

    # --- Tienda: feed de productos -----------------------------------------------------
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

    # --- Oferta: disponibilidad con tres valores, referencia del feed y fallos de enlace --
    op.add_column(
        "oferta",
        sa.Column("disponibilidad", sa.String(length=20), server_default="stock", nullable=False),
    )
    op.execute("UPDATE oferta SET disponibilidad = 'agotada' WHERE NOT disponible")
    op.drop_column("oferta", "disponible")
    op.add_column("oferta", sa.Column("referencia", sa.String(length=200), nullable=True))
    op.create_unique_constraint(op.f("uq_oferta_tienda_id"), "oferta", ["tienda_id", "referencia"])
    op.add_column(
        "oferta",
        sa.Column("enlace_fallos", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )

    # --- Clic: orígenes de la web (catálogo y cuenta) ----------------------------------
    op.drop_constraint(op.f("ck_rec_click_origen"), "rec_click", type_="check")
    op.create_check_constraint(op.f("ck_rec_click_origen"), "rec_click", f"origen IN ({ORIGENES})")

    # --- Staging: ficha propuesta por la IA ---------------------------------------------
    op.add_column(
        "revision_pendiente",
        sa.Column("propuesta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="staging",
    )


def downgrade() -> None:
    op.drop_column("revision_pendiente", "propuesta", schema="staging")

    # Los clics con los orígenes nuevos no caben en el CHECK anterior y se pierden al bajar.
    op.execute("DELETE FROM rec_click WHERE origen IN ('catalogo', 'cuenta')")
    op.drop_constraint(op.f("ck_rec_click_origen"), "rec_click", type_="check")
    op.create_check_constraint(
        op.f("ck_rec_click_origen"), "rec_click", f"origen IN ({ORIGENES_ANTES})"
    )

    op.drop_column("oferta", "enlace_fallos")
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

    op.drop_constraint(op.f("uq_modelo_slug"), "modelo", type_="unique")
    op.drop_column("modelo", "slug")
    op.drop_column("modelo", "nombre")

    op.drop_table("explicacion_cache")
    op.drop_index(op.f("ix_feedback_recomendacion_id"), table_name="feedback")
    op.drop_table("feedback")
    op.drop_table("job_run")
    op.drop_table("metrica_diaria")
    op.drop_index(op.f("ix_events_tipo"), table_name="events")
    op.drop_index(op.f("ix_events_fecha"), table_name="events")
    op.drop_table("events")
