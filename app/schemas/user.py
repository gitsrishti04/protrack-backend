from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: str
    password: str
    role: str