from sqlalchemy import Column, String
from infrastructure.databases.mssql import Base

class Teacher(Base):
    __tablename__ = "teachers"
    teacher_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    specialization = Column(String)