from sqlalchemy import Column, String, Integer
from infrastructure.databases.mssql import Base

class Syllabus(Base):
    __tablename__ = "syllabus"
    syllabus_code = Column(String, primary_key=True)
    syllabus_name = Column(String)
    year = Column(Integer)