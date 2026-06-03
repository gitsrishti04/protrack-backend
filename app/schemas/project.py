from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    status: str = "on_track"
    completion: Optional[int] = 0
    deadline: Optional[str] = None
    team: Optional[str] = ""
