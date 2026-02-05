from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse

SERVER = r'quocthanh'  
DATABASE = 'IGCSE_LearningHub'
USERNAME = 'sa'
PASSWORD = '123'

connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
    f"TrustServerCertificate=yes;"
)

params = urllib.parse.quote_plus(connection_string)

SQLALCHEMY_DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}&charset=utf8"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()