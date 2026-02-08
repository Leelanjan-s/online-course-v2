from pydantic import BaseModel
from typing import List, Optional

# --- User Schemas ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str  # Required for signup
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

# --- Content/Lessons ---
class ContentCreate(BaseModel):
    title: str
    file_url: str
    content_type: str

class ContentResponse(ContentCreate):
    id: int
    class Config:
        from_attributes = True

# --- Quizzes ---
class QuizCreate(BaseModel):
    question: str
    options: str
    correct_answer: str

class QuizResponse(QuizCreate):
    id: int
    class Config:
        from_attributes = True

# --- Course Schemas ---
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
    teacher: str  # Changed from teacher_id to teacher name for display
    teacher_id: int
    contents: List[ContentResponse] = []
    quizzes: List[QuizResponse] = []

    class Config:
        from_attributes = True