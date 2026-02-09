import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.email_utils import send_enrollment_confirm
from app.database import Base, engine, get_db
from app.routes import users, courses, auth
from app.models import User, Course, Enrollment, Content, Quiz
from app.routes.auth import get_password_hash

# Ensure Tables Exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_DIR = Path(__file__).resolve().parent.parent

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
def login_page(): return (BASE_DIR / "templates/login.html").read_text()

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dash(): return (BASE_DIR / "templates/index.html").read_text() 

@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dash(): return (BASE_DIR / "templates/student_dashboard.html").read_text()

@app.get("/teacher/dashboard", response_class=HTMLResponse)
def teacher_dash(): return (BASE_DIR / "templates/teacher_dashboard.html").read_text()

# --- NEW CHECKOUT ROUTE ---
@app.get("/checkout", response_class=HTMLResponse)
def checkout_page():
    return (BASE_DIR / "templates/checkout.html").read_text()

@app.get("/enrollments/")
def get_enrollments(db: Session = Depends(get_db)):
    return db.query(Enrollment).all()

# --- MOCK PAYMENT MODEL ---
class MockPayment(BaseModel):
    course_id: int
    student_id: int
    amount: float

# --- MOCK SUCCESS ENDPOINT ---
@app.post("/payments/mock_success")
def mock_payment_success(data: MockPayment, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Check if enrollment exists
    exists = db.query(Enrollment).filter_by(student_id=data.student_id, course_id=data.course_id).first()
    
    if not exists:
        # 2. Create Enrollment with Fake Transaction ID
        enrollment = Enrollment(
            student_id=data.student_id, 
            course_id=data.course_id, 
            transaction_id=f"PAY_{data.course_id}_{data.student_id}_MOCK",
            completed_videos="",
            completed_quizzes=""
        )
        db.add(enrollment)
        db.commit()
        
        # 3. FETCH DETAILS FOR EMAIL
        student = db.query(User).filter(User.id == data.student_id).first()
        course = db.query(Course).filter(Course.id == data.course_id).first()
        
        teacher_name = "ProLearn Instructor"
        if course:
            teacher = db.query(User).filter(User.id == course.teacher_id).first()
            if teacher:
                teacher_name = teacher.name

        # 4. SEND EMAIL
        if student and course:
            background_tasks.add_task(
                send_enrollment_confirm, 
                email=student.email, 
                name=student.name, 
                course_title=course.title, 
                teacher_name=teacher_name,
                price=course.price
            )

    return {"message": "Enrollment Successful"}

# --- PROGRESS & STATS ---
class ProgressUpdate(BaseModel):
    student_id: int
    course_id: int
    item_id: int
    type: str

@app.post("/progress/mark")
def mark_progress(data: ProgressUpdate, db: Session = Depends(get_db)):
    enrollment = db.query(Enrollment).filter_by(student_id=data.student_id, course_id=data.course_id).first()
    if not enrollment: raise HTTPException(404, detail="Not Found")
    
    current = enrollment.completed_videos if data.type == "video" else enrollment.completed_quizzes
    if current is None: current = ""
    
    if str(data.item_id) not in current.split(","):
        new_val = (current + "," + str(data.item_id)).strip(",")
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
            v_str = e.completed_videos if e.completed_videos else ""
            q_str = e.completed_quizzes if e.completed_quizzes else ""
            done_v = len([x for x in v_str.split(",") if x])
            done_q = len([x for x in q_str.split(",") if x])
            percent = 0
            if total_items > 0:
                percent = int(((done_v + done_q) / total_items) * 100)

            stats.append({
                "student_name": e.student.name,
                "course_title": course.title,
                "video_stats": f"{done_v}/{total_vids}",
                "quiz_stats": f"{done_q}/{total_quiz}",
                "percent": percent
            })
    return stats

@app.get("/courses/{course_id}/learn")
def get_learn_content(course_id: int, student_id: int, db: Session = Depends(get_db)):
    enrollment = db.query(Enrollment).filter_by(course_id=course_id, student_id=student_id).first()
    if not enrollment: raise HTTPException(403, detail="Not Enrolled")
    
    contents = db.query(Content).filter_by(course_id=course_id).all()
    quizzes = db.query(Quiz).filter_by(course_id=course_id).all()
    return {
        "videos": [{"id": c.id, "title": c.title, "url": c.file_url} for c in contents],
        "quizzes": [{"id": q.id, "question": q.question, "options": q.options, "answer": q.correct_answer} for q in quizzes],
        "progress": {"videos": enrollment.completed_videos, "quizzes": enrollment.completed_quizzes}
    }

# --- RESET TOOL ---
@app.post("/debug/reset")
def factory_reset(db: Session = Depends(get_db)):
    db.query(Enrollment).delete()
    db.query(Content).delete()
    db.query(Quiz).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.commit()

    admin = User(name="Admin", email="admin@gmail.com", role="Admin", password_hash=get_password_hash("admin123"), is_verified=True)
    teacher = User(name="Mr. Python", email="teacher@gmail.com", role="Teacher", password_hash=get_password_hash("123456"), is_verified=True)
    student = User(name="Sam", email="student@gmail.com", role="Student", password_hash=get_password_hash("123456"), is_verified=True)
    db.add_all([admin, teacher, student])
    db.commit()
    db.refresh(teacher)

    course = Course(title="Python Mastery", description="Learn Python", price=49.99, teacher_id=teacher.id)
    db.add(course)
    db.commit()
    return {"message": "Reset Done."}


# --- 👇 PASTE THIS AT THE BOTTOM OF app/main.py ---
from app.email_utils import send_email

@app.get("/debug/test-email")
async def test_email_connection():
    try:
        # 1. Print settings to Console (Logs) to verify they exist
        print("--- DEBUG EMAIL SETTINGS ---")
        print(f"User: {os.getenv('MAIL_USERNAME')}")
        print(f"From: {os.getenv('MAIL_FROM')}")
        print("Password: ", "EXISTS" if os.getenv("MAIL_PASSWORD") else "MISSING")
        
        # 2. Try to send a real email synchronously (so we see errors)
        await send_email(
            subject="Test Email from Render",
            recipients=["leelanjans828@gmail.com"], # Sends to yourself
            body="<h1>It Works!</h1><p>If you see this, email is fixed.</p>"
        )
        return {"message": "Email sent successfully! Check your inbox."}
    
    except Exception as e:
        # 3. If it fails, RETURN THE ERROR to the browser
        print(f"❌ EMAIL ERROR: {str(e)}")
        return {"status": "failed", "error": str(e)}