from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from infrastructure.databases.mssql import Base

class StudentAnswer(Base):
    __tablename__ = "student_answers"
    answer_id = Column(Integer, primary_key=True)
    selected_option = Column(String)
    is_correct = Column(Boolean)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.attempt_id"))
    question_id = Column(Integer, ForeignKey("questions.question_id"))