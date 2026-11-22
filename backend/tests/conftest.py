"""Fixtures compartidas.

`db` da una sesión contra el PostgreSQL de DATABASE_URL con las migraciones aplicadas.
Cada test corre dentro de una transacción que se deshace al terminar, así que no deja datos.
Si no hay base de datos (p. ej. Docker apagado), los tests que la usan se saltan.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.config import get_settings


@pytest.fixture(scope="session")
def motor():
    engine = create_engine(get_settings().database_url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except OperationalError:
        pytest.skip("Sin PostgreSQL (arranca 'docker compose up -d')")
    except ProgrammingError:
        pytest.skip("Base de datos sin migrar (ejecuta 'uv run alembic upgrade head')")
    if version is None:
        pytest.skip("Base de datos sin migrar")
    yield engine
    engine.dispose()


@pytest.fixture
def db(motor) -> Iterator[Session]:
    with motor.connect() as conn:
        transaccion = conn.begin()
        # Los commit() del código probado se convierten en savepoints de esta transacción.
        sesion = Session(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield sesion
        finally:
            sesion.close()
            transaccion.rollback()
