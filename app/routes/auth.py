import secrets
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.models import User
from app.email_utils import send_verification_email, send_welcome_email, send_login_alert

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

@router.post("/signup")
async def signup(user: SignupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    token = secrets.token_urlsafe(16)

    hashed_pw = get_password_hash(user.password)
    new_user = User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_pw, 
        role=user.role,
        is_verified=False, 
        verification_token=token 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    if new_user.email:
        background_tasks.add_task(send_verification_email, new_user.email, token)
    
    return {"message": "Signup successful. Please check your email to verify account."}

@router.post("/login")
def login(creds: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first!")

    if user.email:
        background_tasks.add_task(send_login_alert, user.email, user.name)

    return {
        "message": "Login successful", 
        "role": user.role, 
        "user_id": user.id,
        "name": user.name 
    }

@router.get("/verify", response_class=HTMLResponse)
async def verify_email(token: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        return """
        <h1 style='color:red; text-align:center;'>Invalid or Expired Token ❌</h1>
        """
    
    user.is_verified = True
    user.verification_token = None 
    db.commit()

    if user.email:
        background_tasks.add_task(send_welcome_email, user.email, user.name)

    return """
    <div style='text-align:center; padding:50px; font-family:sans-serif;'>
        <h1 style='color:green;'>Email Verified Successfully! ✅</h1>
        <p>You can now close this tab and login to your account.</p>
        <a href='https://online-course-v2.onrender.com/' style='background:blue; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;'>Go to Login</a>
    </div>
    """