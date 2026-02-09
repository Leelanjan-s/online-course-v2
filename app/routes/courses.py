from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models import Course, User, Content, Quiz, Enrollment
from app.schemas import CourseCreate, ContentCreate, QuizCreate
from app.database import get_db
from app.email_utils import send_teacher_assigned_email, send_enrollment_confirm

router = APIRouter(prefix="/courses", tags=["Courses"])

class CourseUpdate(BaseModel):
    title: str
    description: str
    price: float
    teacher_id: int

class EnrollmentRequest(BaseModel):
    student_id: int

# 👇 UPDATE: Added BackgroundTasks
@router.post("/")
def create_course(course: CourseCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == course.teacher_id).first()
    if not teacher or teacher.role != "Teacher":
        raise HTTPException(status_code=400, detail="Invalid Teacher ID")

    c = Course(title=course.title, description=course.description, price=course.price, teacher_id=course.teacher_id)
    db.add(c)
    db.commit()
    db.refresh(c)

    # 👇 FIX: Use background_tasks (Safer)
    if teacher.email:
        background_tasks.add_task(send_teacher_assigned_email, teacher.email, teacher.name, c.title)

    return c

@router.post("/{course_id}/enroll")
def enroll_student(course_id: int, enrollment: EnrollmentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course: raise HTTPException(status_code=404, detail="Course not found")

    student = db.query(User).filter(User.id == enrollment.student_id).first()
    if not student: raise HTTPException(status_code=404, detail="Student not found")

    existing = db.query(Enrollment).filter(Enrollment.student_id == student.id, Enrollment.course_id == course.id).first()
    if existing: raise HTTPException(status_code=400, detail="Already enrolled")

    new_enrollment = Enrollment(student_id=student.id, course_id=course.id)
    db.add(new_enrollment)
    db.commit()

    # 👇 FIX: Use background_tasks (Safer)
    if student.email:
        # We pass teacher name and price to match the new email_utils signature
        teacher_name = "ProLearn Instructor"
        if course.teacher_id:
            teacher = db.query(User).filter(User.id == course.teacher_id).first()
            if teacher: teacher_name = teacher.name
            
        background_tasks.add_task(send_enrollment_confirm, student.email, student.name, course.title, teacher_name, course.price)

    return {"message": "Enrollment successful and email sent"}

@router.get("/")
def list_courses(db: Session = Depends(get_db)):
    results = db.query(Course.id, Course.title, Course.description, Course.price, User.name.label("teacher_name"), Course.teacher_id).join(User, Course.teacher_id == User.id).all()
    return [{"id": r.id, "title": r.title, "description": r.description, "price": r.price, "teacher": r.teacher_name, "teacher_id": r.teacher_id} for r in results]

@router.put("/{course_id}")
def update_course(course_id: int, course_data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    
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
    if not course: raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted"}

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