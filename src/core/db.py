from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db():
    Base.metadata.create_all(engine)  # run once on startup
