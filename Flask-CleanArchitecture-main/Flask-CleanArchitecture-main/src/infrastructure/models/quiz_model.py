from sqlalchemy import Column, Integer, String
from infrastructure.databases.mssql import Base

class Quiz(Base):
    __tablename__ = "quizzes"
    quiz_id = Column(Integer, primary_key=True)
    title = Column(String)
    time_limit = Column(Integer)