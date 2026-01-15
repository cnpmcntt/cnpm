from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float

from infrastructure.databases.base import Base

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    attempt_id = Column(Integer, primary_key=True)
    attempt_date = Column(DateTime)
    score = Column(Float)
    quiz_id = Column(Integer, ForeignKey("quizzes.quiz_id"))
    student_id = Column(String, ForeignKey("students.student_id"))