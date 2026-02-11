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
    
    hashed_pw = get_password_hash(user.password)
    
    token = secrets.token_hex(16)

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
    
    return {"message": "Account created! Please check your email to verify."}

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

@router.get("/verify/{token}", response_class=HTMLResponse)
async def verify_email_click(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        return "<h1 style='color:red;'>Invalid or Expired Token </h1>"
    
    user.is_verified = True
    user.verification_token = None 
    db.commit()
    
    return """
    <html>
        <body style='text-align:center; font-family:sans-serif; padding-top:50px;'>
            <h1 style='color:green;'>Verified Successfully! </h1>
            <p>You can now close this page and log in.</p>
            <a href='https://online-course-v2-production.up.railway.app' style='background:blue; color:white; padding:10px; text-decoration:none;'>Go to Login</a>
        </body>
    </html>
    """