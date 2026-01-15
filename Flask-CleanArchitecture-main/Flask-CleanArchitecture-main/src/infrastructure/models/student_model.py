from sqlalchemy import Column, String, ForeignKey
from infrastructure.databases.mssql import Base

class Student(Base):
    __tablename__ = "students"
    student_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True)
    target_grade = Column(String)
    current_level = Column(String)
    teacher_id = Column(String, ForeignKey("teachers.teacher_id"))