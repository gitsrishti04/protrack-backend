import os
from jose import jwt
from datetime import datetime, timedelta

# Read from environment variable; fall back to dev default only in development.
# In production set:  export JWT_SECRET_KEY="<strong-random-secret>"
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "protrack-dev-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
