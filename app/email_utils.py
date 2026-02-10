import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# Configuration
SENDER_EMAIL = os.getenv("MAIL_USERNAME", "leelanjans828@gmail.com") 
SENDER_NAME = "ProLearn Admin"

def send_brevo_email(to_email: str, to_name: str, subject: str, html_content: str):
    if not BREVO_API_KEY:
        print("❌ Error: BREVO_API_KEY is missing in Environment Variables.")
        return

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 201:
            print(f"✅ Email sent successfully to {to_email}")
        else:
            print(f"⚠️ Email Failed: {response.text}")
    except Exception as e:
        print(f"❌ Network Error sending email: {e}")

async def send_email(subject: str, recipients: list, body: str):
    for email_addr in recipients:
        send_brevo_email(email_addr, "User", subject, body)

async def send_welcome_email(email: str, name: str):
    html = f"<h1>Welcome {name}!</h1><p>Your account is active. You can login now.</p>"
    send_brevo_email(email, name, "Welcome to ProLearn", html)

async def send_login_alert(email: str, name: str):
    html = f"<p>Hello {name}, we detected a new login to your account.</p>"
    send_brevo_email(email, name, "Login Alert", html)

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    html = f"""
    <h1>Enrollment Confirmed</h1>
    <p>Hi {name}, you have enrolled in <b>{course_title}</b>.</p>
    <p>Instructor: {teacher_name}</p>
    """
    send_brevo_email(email, name, f"Enrolled: {course_title}", html)

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    html = f"<p>Hello {teacher_name}, you have been assigned to teach <b>{course_title}</b>.</p>"
    send_brevo_email(email, teacher_name, "New Course Assignment", html)

async def send_verification_email(email: str, token: str):
    pass