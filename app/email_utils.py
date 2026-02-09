import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "leelanjans828@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),  # Reads from Render Environment
    MAIL_FROM=os.getenv("MAIL_FROM", "leelanjans828@gmail.com"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
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

# 👇 RESTORED: This was missing in the last step!
async def send_login_alert(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h3 style="color: #EF4444;">🔐 Security Alert</h3>
        <p>Hello {name},</p>
        <p>We noticed a new login to your ProLearn account.</p>
    </div>
    """
    await send_email("New Login Detected", [email], html)

async def send_enrollment_confirm(email: str, name: str, course_title: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #4F46E5;">Enrollment Confirmed! 🎓</h2>
        <p>Hi {name},</p>
        <p>You have successfully enrolled in <strong>{course_title}</strong>.</p>
        <p>Happy Learning!</p>
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