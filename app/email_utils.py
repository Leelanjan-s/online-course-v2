import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

# 👇 OUTLOOK / HOTMAIL SETTINGS
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    
    # 👇 Outlook uses Port 587
    MAIL_PORT=587,
    MAIL_SERVER="smtp.office365.com",
    
    # 👇 Standard Security for Outlook
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False 
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

# 👇 Verification Email
async def send_verification_email(email: str, token: str):
    verify_url = f"https://online-course-v2.onrender.com/auth/verify?token={token}"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; max-width: 500px;">
        <h2 style="color: #4F46E5;">Verify Your Account 🔒</h2>
        <p>Welcome! Please click the button below to activate your account.</p>
        <br>
        <a href="{verify_url}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Verify Email</a>
    </div>
    """
    await send_email("Action Required: Verify Email", [email], html)

async def send_welcome_email(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #10B981;">Account Verified! ✅</h2>
        <p>Welcome to ProLearn, {name}. You can now login and explore courses.</p>
    </div>
    """
    await send_email("Welcome to ProLearn!", [email], html)

async def send_login_alert(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h3 style="color: #EF4444;">🔐 Security Alert</h3>
        <p>Hello {name}, we noticed a new login to your account.</p>
    </div>
    """
    await send_email("New Login Detected", [email], html)

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #4F46E5;">Enrollment Confirmed! 🎓</h2>
        <p>Hi <strong>{name}</strong>,</p>
        <p>You are now enrolled in <strong>{course_title}</strong>.</p>
        <p><strong>Instructor:</strong> {teacher_name}</p>
        <a href="https://online-course-v2.onrender.com/student/dashboard" style="background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
    </div>
    """
    await send_email(f"Enrollment: {course_title}", [email], html)

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee;">
        <h2 style="color: #4F46E5;">New Course Assignment 👨‍🏫</h2>
        <p>Hello {teacher_name}, you are the instructor for <strong>{course_title}</strong>.</p>
    </div>
    """
    await send_email(f"Course Assigned: {course_title}", [email], html)