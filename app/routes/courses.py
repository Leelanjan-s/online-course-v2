from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models import Course, User, Content, Quiz, Enrollment
from app.schemas import CourseCreate, ContentCreate, QuizCreate
from app.database import get_db
# 👇 NEW: Import the email functions
from app.email_utils import send_teacher_assigned_email, send_enrollment_confirm

router = APIRouter(prefix="/courses", tags=["Courses"])

# --- Schema for Updating ---
class CourseUpdate(BaseModel):
    title: str
    description: str
    price: float
    teacher_id: int

# --- Schema for Enrollment ---
class EnrollmentRequest(BaseModel):
    student_id: int

# 👇 CHANGED to 'async def' to allow email sending
@router.post("/")
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == course.teacher_id).first()
    if not teacher or teacher.role != "Teacher":
        raise HTTPException(status_code=400, detail="Invalid Teacher ID")

    c = Course(title=course.title, description=course.description, price=course.price, teacher_id=course.teacher_id)
    db.add(c)
    db.commit()
    db.refresh(c)

    # 👇 SEND EMAIL TO TEACHER
    if teacher.email:
        await send_teacher_assigned_email(teacher.email, teacher.name, c.title)

    return c

# 👇 NEW ENDPOINT: Enrolls a student and sends the email
@router.post("/{course_id}/enroll")
async def enroll_student(course_id: int, enrollment: EnrollmentRequest, db: Session = Depends(get_db)):
    # 1. Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Check if student exists
    student = db.query(User).filter(User.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 3. Check if already enrolled
    existing = db.query(Enrollment).filter(Enrollment.student_id == student.id, Enrollment.course_id == course.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")

    # 4. Create Enrollment
    new_enrollment = Enrollment(student_id=student.id, course_id=course.id)
    db.add(new_enrollment)
    db.commit()

    # 👇 SEND EMAIL TO STUDENT
    if student.email:
        await send_enrollment_confirm(student.email, student.name, course.title)

    return {"message": "Enrollment successful and email sent"}

@router.get("/")
def list_courses(db: Session = Depends(get_db)):
    results = db.query(Course.id, Course.title, Course.description, Course.price, User.name.label("teacher_name"), Course.teacher_id).join(User, Course.teacher_id == User.id).all()
    return [{"id": r.id, "title": r.title, "description": r.description, "price": r.price, "teacher": r.teacher_name, "teacher_id": r.teacher_id} for r in results]

@router.put("/{course_id}")
def update_course(course_id: int, course_data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course.title = course_data.title
    course.description = course_data.description
    course.price = course_data.price
    course.teacher_id = course_data.teacher_id
    
    db.commit()
    db.refresh(course)
    return {"message": "Course updated successfully"}

@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}

# --- Content & Quizzes ---
@router.post("/{course_id}/content")
def add_content(course_id: int, content: ContentCreate, db: Session = Depends(get_db)):
    c = Content(**content.dict(), course_id=course_id)
    db.add(c)
    db.commit()
    return {"message": "Content added"}

@router.post("/{course_id}/quiz")
def add_quiz(course_id: int, quiz: QuizCreate, db: Session = Depends(get_db)):
    q = Quiz(**quiz.dict(), course_id=course_id)
    db.add(q)
    db.commit()
    return {"message": "Quiz added"}