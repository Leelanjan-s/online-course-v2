import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION (The "Loose" Fix) ---
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    
    # 👇 SETTINGS FOR RENDER FREE TIER
    MAIL_PORT=587,              # Back to 587 (Standard)
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,         # Must be True for 587
    MAIL_SSL_TLS=False,         # Must be False for 587
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False        # 👈 THIS IS THE FIX (Prevents timeouts)
)

async def send_email(subject: str, recipients: list[EmailStr], body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)

# --- TEMPLATES ---

async def send_welcome_email(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #4F46E5;">Welcome to ProLearn, {name}! 🚀</h2>
        <p>You have successfully created your account.</p>
    </div>
    """
    await send_email("Welcome to ProLearn!", [email], html)

async def send_login_alert(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h3 style="color: #EF4444;">🔐 Security Alert</h3>
        <p>Hello {name},</p>
        <p>We noticed a new login to your ProLearn account.</p>
    </div>
    """
    await send_email("New Login Detected", [email], html)

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str = "ProLearn", price: float = 0.0):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #4F46E5;">Enrollment Confirmed! 🎓</h2>
        <p>Hi <strong>{name}</strong>,</p>
        <p>You are now enrolled in:</p>
        <h3 style="background-color: #f3f4f6; padding: 15px;">{course_title}</h3>
        <p><strong>Instructor:</strong> {teacher_name}</p>
        <p><strong>Amount Paid:</strong> ₹{price}</p>
        <br>
        <a href="https://online-course-v2.onrender.com/student/dashboard" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
    </div>
    """
    await send_email(f"Enrollment: {course_title}", [email], html)

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #4F46E5;">New Course Assignment 👨‍🏫</h2>
        <p>Hello <strong>{teacher_name}</strong>,</p>
        <p>You have been assigned as the instructor for:</p>
        <h3 style="background-color: #f3f4f6; padding: 10px;">{course_title}</h3>
        <p>Login to your dashboard to start adding content.</p>
    </div>
    """
    await send_email(f"Course Assigned: {course_title}", [email], html)