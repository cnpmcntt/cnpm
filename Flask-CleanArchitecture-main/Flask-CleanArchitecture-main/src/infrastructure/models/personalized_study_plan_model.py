from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from infrastructure.databases.mssql import Base

class PersonalizedStudyPlan(Base):
    __tablename__ = "study_plans"
    plan_id = Column(Integer, primary_key=True)
    created_date = Column(DateTime)
    goal_description = Column(String)
    student_id = Column(String, ForeignKey("students.student_id"))