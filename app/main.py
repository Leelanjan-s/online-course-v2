import os
import stripe
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.email_utils import send_enrollment_confirm, send_email
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

# --- STRIPE CONFIGURATION ---
# 👇 PASTE YOUR KEYS HERE
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    print("⚠️ WARNING: Stripe Keys are missing! Check your .env file.")

stripe.api_key = STRIPE_SECRET_KEY

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


# --- STRIPE PAYMENT ROUTES ---

class StripeCheckoutRequest(BaseModel):
    course_id: int
    student_id: int
    price: float
    course_title: str

@app.post("/create-checkout-session")
def create_checkout_session(data: StripeCheckoutRequest):
    try:
        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': data.course_title,
                    },
                    'unit_amount': int(data.price * 100), # Amount in paisa
                },
                'quantity': 1,
            }],
            mode='payment',
            # 👇 Redirect URLs (Points to Localhost for testing)
            # 👇 UPDATED FOR RENDER DEPLOYMENT
            success_url=f"https://online-course-v2.onrender.com/payment/success?session_id={{CHECKOUT_SESSION_ID}}&course_id={data.course_id}&student_id={data.student_id}",
            cancel_url="https://online-course-v2.onrender.com/student/dashboard",
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payment/success")
def payment_success(session_id: str, course_id: int, student_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Verify Payment with Stripe
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            raise HTTPException(status_code=400, detail="Payment failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid Session")

    # 2. Check Enrollment
    exists = db.query(Enrollment).filter_by(student_id=student_id, course_id=course_id).first()
    if not exists:
        # 3. Enroll Student
        enrollment = Enrollment(
            student_id=student_id, 
            course_id=course_id, 
            transaction_id=f"STRIPE_{session.payment_intent}",
            completed_videos="",
            completed_quizzes=""
        )
        db.add(enrollment)
        db.commit()

        # 4. Send Email
        student = db.query(User).filter(User.id == student_id).first()
        course = db.query(Course).filter(Course.id == course_id).first()
        
        teacher_name = "ProLearn Instructor"
        if course.teacher_id:
            t = db.query(User).filter(User.id == course.teacher_id).first()
            if t: teacher_name = t.name
            
        if student and course:
            background_tasks.add_task(
                send_enrollment_confirm, 
                student.email, student.name, course.title, teacher_name, course.price
            )

    # 5. Redirect to Dashboard with Success Message
    return RedirectResponse(url="/student/dashboard")


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

# --- DEBUG EMAIL ROUTE ---
@app.get("/debug/test-email")
async def test_email_connection():
    try:
        # 1. Print settings to Console (Logs) to verify they exist
        print("--- DEBUG EMAIL SETTINGS ---")
        print(f"User: {os.getenv('MAIL_USERNAME')}")
        print(f"From: {os.getenv('MAIL_FROM')}")
        print("Password: ", "EXISTS" if os.getenv("MAIL_PASSWORD") else "MISSING")
        
        # 2. Try to send a real email synchronously
        await send_email(
            subject="Test Email from Render",
            recipients=["leelanjans828@gmail.com"],
            body="<h1>It Works!</h1><p>If you see this, email is fixed.</p>"
        )
        return {"message": "Email sent successfully! Check your inbox."}
    
    except Exception as e:
        print(f"❌ EMAIL ERROR: {str(e)}")
        return {"status": "failed", "error": str(e)}