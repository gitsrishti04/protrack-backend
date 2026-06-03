from pydantic import BaseModel
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    status: str = "pending"
    description: Optional[str] = None   
    assigned_to: Optional[str] = None