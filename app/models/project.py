from sqlalchemy import Column, Integer, String
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    status = Column(String)
    completion = Column(Integer)
    deadline = Column(String)
    team = Column(String)