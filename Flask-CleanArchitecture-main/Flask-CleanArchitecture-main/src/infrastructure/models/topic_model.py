from sqlalchemy import Column, Integer, String, Float, ForeignKey
from infrastructure.databases.mssql import Base

class Topic(Base):
    __tablename__ = "topics"
    topic_id = Column(Integer, primary_key=True)
    topic_name = Column(String)
    weighting = Column(Float)
    syllabus_code = Column(String, ForeignKey("syllabus.syllabus_code"))