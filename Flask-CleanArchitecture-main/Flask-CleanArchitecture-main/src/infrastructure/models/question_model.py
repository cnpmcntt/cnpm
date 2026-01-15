from sqlalchemy import Column, Integer, String
from infrastructure.databases.mssql import Base

class Question(Base):
    __tablename__ = "questions"
    question_id = Column(Integer, primary_key=True)
    content_text = Column(String)
    difficulty_level = Column(String)
    correct_answer = Column(String)