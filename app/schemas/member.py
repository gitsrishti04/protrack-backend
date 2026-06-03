from pydantic import BaseModel
from typing import Optional

class MemberCreate(BaseModel):
    name: str
    role: str
    email: Optional[str] = None   # links to a team_lead user account