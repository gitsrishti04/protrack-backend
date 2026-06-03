from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.utils.deps import get_current_user

router = APIRouter()


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# REGISTER
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "User created successfully",
        "email": new_user.email,
        "role": new_user.role
    }


# REGISTER via dashboard (enforces role hierarchy)
@router.post("/users")
def create_user_by_admin(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    caller_role = current_user.get("role")
    if caller_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    hierarchy = {"team_lead": 0, "admin": 1, "super_admin": 2}
    caller_level = hierarchy.get(caller_role, 0)
    target_level = hierarchy.get(user.role, 0)

    if target_level >= caller_level:
        raise HTTPException(
            status_code=403,
            detail=f"You cannot create a {user.role} account"
        )

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email, "role": new_user.role}



# LOGIN (OAuth2 compatible)
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "name": user.name
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# GET CURRENT USER PROFILE (all roles — uses JWT identity)
@router.get("/users/me")
def get_me(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    email = current_user.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


# GET ALL USERS (admin + super_admin only, paginated, searchable)
@router.get("/users")
def get_users(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    total = query.count()
    offset = (page - 1) * limit
    users = query.offset(offset).limit(limit).all()
    
    items = [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
    
    return {
        "items": items,
        "total": total
    }


# DELETE USER (role-hierarchy enforced)
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    caller_role = current_user.get("role")
    if caller_role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Role hierarchy: you cannot delete users at or above your own level
    hierarchy = {"team_lead": 0, "admin": 1, "super_admin": 2}
    caller_level = hierarchy.get(caller_role, 0)
    target_level = hierarchy.get(user.role, 0)

    if target_level >= caller_level:
        raise HTTPException(
            status_code=403,
            detail=f"You cannot delete a {user.role} account"
        )

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}