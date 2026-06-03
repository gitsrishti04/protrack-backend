from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class ProgressHistory(Base):
    __tablename__ = "progress_history"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    progress   = Column(Integer, nullable=False)          # 0–100
    task_name  = Column(String, nullable=True)
    comments   = Column(String, nullable=True)
    status     = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
