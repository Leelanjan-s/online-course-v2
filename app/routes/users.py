from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import User, Course, Enrollment
from app.schemas import UserCreate
from app.database import get_db
from app.routes.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password provided by frontend (or default)
    hashed_pw = get_password_hash(user.password) 
    
    u = User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_pw, 
        role=user.role,
        is_verified=True # Admin-created users are auto-verified
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cascade delete
    db.query(Course).filter(Course.teacher_id == user_id).delete()
    db.query(Enrollment).filter(Enrollment.student_id == user_id).delete()
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}