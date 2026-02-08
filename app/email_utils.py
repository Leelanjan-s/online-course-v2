from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

# --- EMAIL CONFIGURATION ---
conf = ConnectionConfig(
    MAIL_USERNAME="leelanjans828@gmail.com",
    
    # 🔴 UPDATED PASSWORD (Spaces removed)
    MAIL_PASSWORD="sdujhruuyouppqxw", 
    
    MAIL_FROM="leelanjans828@gmail.com",
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
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #4F46E5;">Welcome to ProLearn, {name}! 🚀</h2>
        <p>You have successfully created your account.</p>
        <p>Explore our catalog and start building your future today.</p>
    </div>
    """
    await send_email("Welcome to ProLearn!", [email], html)

async def send_login_alert(email: str, name: str):
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h3>🔐 Security Alert</h3>
        <p>Hello {name},</p>
        <p>We noticed a new login to your ProLearn account.</p>
    </div>
    """
    await send_email("New Login Detected", [email], html)

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    html = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #4F46E5;">
            <h1 style="color: #4F46E5; margin: 0;">ProLearn</h1>
            <p style="color: #666; margin-top: 5px;">Enrollment Confirmation</p>
        </div>
        <div style="padding: 20px 0;">
            <p style="font-size: 16px;">Hi <strong>{name}</strong>,</p>
            <p>Thank you for enrolling! You have successfully secured your spot in:</p>
            <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #4F46E5;">
                <h2 style="margin: 0; color: #1f2937;">{course_title}</h2>
                <p style="margin: 5px 0 0; color: #6b7280;">Instructor: <strong>{teacher_name}</strong></p>
                <p style="margin: 5px 0 0; color: #6b7280;">Amount Paid: <strong>₹{price}</strong></p>
            </div>
            <p>Your learning journey begins now.</p>
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://127.0.0.1:8001/student/dashboard" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Go to Dashboard</a>
            </div>
        </div>
    </div>
    """
    await send_email(f"🎓 Enrollment Confirmed: {course_title}", [email], html)