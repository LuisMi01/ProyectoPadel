"""Base de datos de pruebas.

Los tests que piden el fixture `db` o `cliente` usan una base aparte (`padel_test` en el
PostgreSQL de docker compose), con las migraciones aplicadas. Cada test corre dentro de una
transacción que se deshace al terminar, así que no deja datos. Si no hay PostgreSQL (por ejemplo,
en la CI), esos tests se saltan.
"""

import os
from pathlib import Path

# Antes de importar la aplicación: la API y Alembic leen DATABASE_URL al arrancar.
URL_PRUEBAS = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://padel:padel@localhost:5432/padel_test"
)
os.environ["DATABASE_URL"] = URL_PRUEBAS

import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def _preparar_bd() -> bool:
    url = make_url(URL_PRUEBAS)
    admin = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 2},
    )
    try:
        with admin.connect() as conexion:
            existe = conexion.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :nombre"), {"nombre": url.database}
            )
            if not existe:
                conexion.execute(text(f'CREATE DATABASE "{url.database}"'))
    except OperationalError:
        return False
    finally:
        admin.dispose()

    from alembic.config import Config

    from alembic import command

    command.upgrade(Config(str(BACKEND / "alembic.ini")), "head")
    return True


@pytest.fixture(scope="session")
def motor_bd():
    if not _preparar_bd():
        pytest.skip("Sin PostgreSQL de pruebas (arranca la base con: docker compose up -d)")
    from app.db.session import engine

    return engine


@pytest.fixture
def db(motor_bd):
    conexion = motor_bd.connect()
    transaccion = conexion.begin()
    # Los commit() de los servicios se quedan en puntos de guardado dentro de la transacción.
    sesion = Session(
        bind=conexion, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    yield sesion
    sesion.close()
    transaccion.rollback()
    conexion.close()


@pytest.fixture
def cliente(db):
    from fastapi.testclient import TestClient

    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def catalogo(db):
    """Catálogo de ejemplo cargado en la base de pruebas."""
    from app.semillas import cargar

    cargar(db)
    return db
