from sqlalchemy import Column, Integer, String, ForeignKey
from infrastructure.databases.mssql import Base

class SubTopic(Base):
    __tablename__ = "sub_topics"
    subtopic_id = Column(Integer, primary_key=True)
    subtopic_name = Column(String)
    description = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"))