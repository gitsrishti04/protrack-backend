from fastapi import APIRouter, Depends
from app.utils.deps import get_current_user
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

@router.get("/protected")
def protected(user: dict = Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": user
    }