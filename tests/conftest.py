import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine

RAIZ = Path(__file__).resolve().parent.parent


def url_banco():
    load_dotenv(RAIZ / ".env")
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@pytest.fixture(scope="session")
def engine():
    url = url_banco()
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")
    eng = create_engine(url)
    yield eng
    eng.dispose()


@pytest.fixture
def conn(engine):
    with engine.connect() as conexao:
        transacao = conexao.begin()
        yield conexao
        transacao.rollback()
