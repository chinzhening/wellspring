from sqlalchemy import text

from core.db import SessionLocal, engine


def test_engine_exists():
    assert engine is not None


def test_database_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_executes_query():
    with SessionLocal() as session:
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_pgvector_extension():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
        )
        assert result.scalar() == 1, "pgvector extension is not installed"


def test_pgtrgm_extension():
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_trgm'")
        )
        assert result.scalar() == 1, "pg_trgm extension is not installed"
