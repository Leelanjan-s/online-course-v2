import secrets
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.models import User

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
    
    new_user = User(
        name=user.name, 
        email=user.email, 
        password_hash=hashed_pw, 
        role=user.role,
        is_verified=True,     
        verification_token="auto-verified" 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    
    return {"message": "Account created successfully. You can login now."}

@router.post("/login")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    

    return {
        "message": "Login successful", 
        "role": user.role, 
        "user_id": user.id,
        "name": user.name 
    }

@router.get("/verify", response_class=HTMLResponse)
async def verify_email(token: str):
    return "<h1 style='color:green; text-align:center;'>Already Verified! ✅</h1>"