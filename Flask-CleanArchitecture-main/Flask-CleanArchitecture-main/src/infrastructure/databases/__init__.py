from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Config
from infrastructure.databases.base import Base

# Create engine (SQLite)
engine = create_engine(
    Config.DATABASE_URI,
    echo=True,            # in SQL ra terminal (rất dễ debug)
    future=True
)

# Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db(app):
    """Create all tables from models"""
    Base.metadata.create_all(bind=engine)
