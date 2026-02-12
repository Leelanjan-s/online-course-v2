import os
import stripe
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

# Import email functions
from app.email_utils import send_welcome_email, send_enrollment_confirm, send_teacher_assigned_email
from app.database import Base, engine, get_db
# ✅ FIX 1: REMOVED 'courses' from here. Only import users and auth.
from app.routes import users, auth 
from app.models import User, Course, Enrollment, Content, Quiz, Question

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ FIX 2: Only include these two. We handle courses manually below.
app.include_router(auth.router)
app.include_router(users.router)
# app.include_router(courses.router) <--- THIS WAS THE PROBLEM. IT IS GONE NOW.

app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_DIR = Path(__file__).resolve().parent.parent

STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# ✅ Make sure this is your correct Railway URL
YOUR_DOMAIN = "https://online-course-v2-production.up.railway.app"

# --- PAGE ROUTES ---
@app.get("/", response_class=HTMLResponse)
def login_page(): return (BASE_DIR / "templates/login.html").read_text()

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dash(): return (BASE_DIR / "templates/index.html").read_text() 

@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dash(): return (BASE_DIR / "templates/student_dashboard.html").read_text()

@app.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dash(): return (BASE_DIR / "templates/teacher_dashboard.html").read_text()

@app.get("/checkout", response_class=HTMLResponse)
def checkout_page(): return (BASE_DIR / "templates/checkout.html").read_text()

@app.get("/enrollments/")
def get_enrollments(db: Session = Depends(get_db)):
    return db.query(Enrollment).all()

# --- PAYMENT ROUTES ---
class StripeCheckoutRequest(BaseModel):
    course_id: int
    student_id: int
    price: float
    course_title: str

@app.post("/create-checkout-session")
def create_checkout_session(data: StripeCheckoutRequest):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price_data': {'currency': 'inr', 'product_data': {'name': data.course_title}, 'unit_amount': int(data.price * 100)}, 'quantity': 1}],
            mode='payment',
            success_url=f"{YOUR_DOMAIN}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&course_id={data.course_id}&student_id={data.student_id}",
            cancel_url=f"{YOUR_DOMAIN}/student/dashboard",
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment/success")
def payment_success(session_id: str, course_id: int, student_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        if stripe.checkout.Session.retrieve(session_id).payment_status != 'paid': raise HTTPException(400)
    except: pass 
    
    if not db.query(Enrollment).filter_by(student_id=student_id, course_id=course_id).first():
        db.add(Enrollment(student_id=student_id, course_id=course_id, transaction_id=f"STRIPE_{session_id}"))
        db.commit()
        
        student = db.query(User).filter(User.id == student_id).first()
        course = db.query(Course).filter(Course.id == course_id).first()
        if student and course and student.email:
            background_tasks.add_task(send_enrollment_confirm, student.email, student.name, course.title)

    return RedirectResponse(url="/student/dashboard")

# --- COURSE ROUTES (Moved here to avoid conflicts) ---

class CourseCreate(BaseModel):
    title: str
    description: str
    price: float
    teacher_id: int

@app.get("/courses/")
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

@app.post("/courses/")
def create_course(course: CourseCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_course = Course(title=course.title, description=course.description, price=course.price, teacher_id=course.teacher_id)
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    teacher = db.query(User).filter(User.id == course.teacher_id).first()
    if teacher and teacher.email:
        background_tasks.add_task(send_teacher_assigned_email, teacher.email, teacher.name, course.title)
    return new_course

@app.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    db.query(Course).filter(Course.id == course_id).delete()
    db.commit()
    return {"message": "Deleted"}

class ContentCreate(BaseModel):
    title: str
    file_url: str
    content_type: str

@app.post("/courses/{course_id}/content")
def add_content(course_id: int, content: ContentCreate, db: Session = Depends(get_db)):
    db.add(Content(**content.dict(), course_id=course_id))
    db.commit()
    return {"message": "Content added"}

# --- QUIZ ROUTES (The correct ones) ---

class QuestionCreate(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str

class QuizCreate(BaseModel):
    title: str
    questions: List[QuestionCreate]

@app.post("/courses/{course_id}/quiz")
def create_quiz(course_id: int, quiz_data: QuizCreate, db: Session = Depends(get_db)):
    # 1. Create Quiz
    new_quiz = Quiz(title=quiz_data.title, course_id=course_id)
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)

    # 2. Add Questions
    for q in quiz_data.questions:
        db.add(Question(quiz_id=new_quiz.id, **q.dict()))
    
    db.commit()
    return {"message": "Quiz created successfully"}

@app.delete("/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        db.delete(quiz)
        db.commit()
    return {"message": "Deleted"}

@app.get("/courses/{course_id}/learn")
def get_learn_content(course_id: int, student_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course: raise HTTPException(404, detail="Course not found")

    is_teacher = (course.teacher_id == student_id)
    enrollment = db.query(Enrollment).filter_by(course_id=course_id, student_id=student_id).first()

    if not is_teacher and not enrollment: raise HTTPException(403, detail="Not Enrolled")
    
    all_content = db.query(Content).filter_by(course_id=course_id).all()
    quizzes = db.query(Quiz).filter_by(course_id=course_id).all()
    
    formatted_quizzes = []
    for q in quizzes:
        qs = db.query(Question).filter_by(quiz_id=q.id).all()
        formatted_quizzes.append({
            "id": q.id, "title": q.title,
            "questions": [{"id": x.id, "question": x.question_text, "options": [x.option_a, x.option_b, x.option_c, x.option_d], "answer": x.correct_answer} for x in qs]
        })

    prog_v = enrollment.completed_videos if enrollment else ""
    prog_q = enrollment.completed_quizzes if enrollment else ""

    return {
        "videos": [{"id": c.id, "title": c.title, "url": c.file_url} for c in all_content if c.content_type == "video"],
        "resources": [{"id": c.id, "title": c.title, "url": c.file_url} for c in all_content if c.content_type != "video"],
        "quizzes": formatted_quizzes,
        "progress": {"videos": prog_v, "quizzes": prog_q}
    }

# --- PROGRESS ROUTES ---

class ProgressUpdate(BaseModel):
    student_id: int
    course_id: int
    item_id: int
    type: str

@app.post("/progress/mark")
def mark_progress(data: ProgressUpdate, db: Session = Depends(get_db)):
    enrollment = db.query(Enrollment).filter_by(student_id=data.student_id, course_id=data.course_id).first()
    if not enrollment: raise HTTPException(404)
    current = enrollment.completed_videos if data.type == "video" else enrollment.completed_quizzes
    if str(data.item_id) not in (current or "").split(","):
        new_val = ((current or "") + "," + str(data.item_id)).strip(",")
        if data.type == "video": enrollment.completed_videos = new_val
        else: enrollment.completed_quizzes = new_val
        db.commit()
    return {"message": "Updated"}

@app.get("/teacher/stats/{teacher_id}")
def get_teacher_stats(teacher_id: int, db: Session = Depends(get_db)):
    courses = db.query(Course).filter(Course.teacher_id == teacher_id).all()
    stats = []
    for course in courses:
        enrollments = db.query(Enrollment).filter(Enrollment.course_id == course.id).all()
        total_vids = db.query(Content).filter(Content.course_id == course.id).count()
        total_quiz = db.query(Quiz).filter(Quiz.course_id == course.id).count()
        total_items = total_vids + total_quiz
        for e in enrollments:
            done_v = len([x for x in (e.completed_videos or "").split(",") if x])
            done_q = len([x for x in (e.completed_quizzes or "").split(",") if x])
            percent = int(((done_v + done_q) / total_items) * 100) if total_items > 0 else 0
            stats.append({"student_name": e.student.name, "course_title": course.title, "video_stats": f"{done_v}/{total_vids}", "quiz_stats": f"{done_q}/{total_quiz}", "percent": percent})
    return stats

@app.get("/test-email")
async def debug_email(): return {"message": "Email endpoint"}