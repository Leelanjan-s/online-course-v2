from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import User, Course, Enrollment
from app.schemas import UserCreate
from app.database import get_db
from app.routes.auth import get_password_hash
from app.email_utils import send_welcome_email

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
async def add_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password) 
    
    u = User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_pw, 
        role=user.role,
        is_verified=True 
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
    
    db.query(Course).filter(Course.teacher_id == user_id).delete()
    db.query(Enrollment).filter(Enrollment.student_id == user_id).delete()
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}