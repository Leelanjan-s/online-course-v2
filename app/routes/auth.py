from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.models import User
from app.email_utils import send_welcome_email, send_login_alert

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- SIGNUP ROUTE ---
@router.post("/signup")
def signup(user: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Check if email exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Create User
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_pw, 
        role=user.role,
        is_verified=False 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 👇 SEND WELCOME EMAIL (Works for Teacher & Student)
    if new_user.email:
        background_tasks.add_task(send_welcome_email, new_user.email, new_user.name)
    
    return {"message": "User created successfully"}

# --- LOGIN ROUTE ---
@router.post("/login")
def login(creds: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # 👇 SEND LOGIN ALERT (Works for Teacher & Student)
    if user.email:
        background_tasks.add_task(send_login_alert, user.email, user.name)

    return {
        "message": "Login successful", 
        "role": user.role, 
        "user_id": user.id,
        "name": user.name 
    }