from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.databases.base import Base

DATABASE_URI = "sqlite:///default.db"

engine = create_engine(
    DATABASE_URI,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

session = SessionLocal()

def init_mssql(app):
    Base.metadata.create_all(bind=engine)
