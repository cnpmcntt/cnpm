from sqlalchemy import Column, Integer, Float, String, ForeignKey
from infrastructure.databases.mssql import Base

class KnowledgeMastery(Base):
    __tablename__ = "knowledge_mastery"
    mastery_id = Column(Integer, primary_key=True)
    mastery_score = Column(Float)
    status = Column(String)
    student_id = Column(String, ForeignKey("students.student_id"))
    subtopic_id = Column(Integer, ForeignKey("sub_topics.subtopic_id"))