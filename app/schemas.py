from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    name: str
    email: str
    password: str  
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class ContentCreate(BaseModel):
    title: str
    file_url: str
    content_type: str

class ContentResponse(ContentCreate):
    id: int
    class Config:
        from_attributes = True

class QuizCreate(BaseModel):
    question: str
    options: str
    correct_answer: str

class QuizResponse(QuizCreate):
    id: int
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = "No description"
    price: float = 0.0
    teacher_id: int

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = ""
    price: float
    teacher: str  
    teacher_id: int
    contents: List[ContentResponse] = []
    quizzes: List[QuizResponse] = []

    class Config:
        from_attributes = True