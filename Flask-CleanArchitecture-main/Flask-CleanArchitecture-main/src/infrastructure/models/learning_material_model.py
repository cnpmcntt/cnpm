from sqlalchemy import Column, Integer, String
from infrastructure.databases.mssql import Base

class LearningMaterial(Base):
    __tablename__ = "learning_materials"
    material_id = Column(Integer, primary_key=True)
    type = Column(String)
    content_url = Column(String)
    duration_minutes = Column(Integer)