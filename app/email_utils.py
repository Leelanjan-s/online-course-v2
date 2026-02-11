import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

SENDER_EMAIL = "leelanjans828@gmail.com" 
SENDER_NAME = "ProLearn Admin"
BASE_URL = "https://online-course-v2-production.up.railway.app"

def send_brevo_email(to_email: str, to_name: str, subject: str, html_content: str):
    if not BREVO_API_KEY:
        print(" Error: BREVO_API_KEY is missing.")
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
            print(f" Email sent successfully to {to_email}")
        else:
            print(f" Brevo Error: {response.status_code} - {response.text}") 
    except Exception as e:
        print(f" Network Error: {e}")

async def send_verification_email(email: str, token: str):
    verification_link = f"{BASE_URL}/auth/verify/{token}"
    
    html = f"""
    <h1>Verify Your Account 🔒</h1>
    <p>Click the link below to activate your account:</p>
    <a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a>
    <p>Or copy this link: {verification_link}</p>
    """
    send_brevo_email(email, "New User", "Verify Your Email", html)

async def send_welcome_email(email: str, name: str):
    html = f"<h1>Welcome {name}!</h1><p>Your account is verified and active.</p>"
    send_brevo_email(email, name, "Welcome to ProLearn", html)

async def send_login_alert(email: str, name: str):
    html = f"<p>Hello {name}, we detected a new login.</p>"
    send_brevo_email(email, name, "Login Alert", html)

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    html = f"<h1>Enrolled!</h1><p>You joined <b>{course_title}</b>.</p>"
    send_brevo_email(email, name, f"Enrolled: {course_title}", html)

async def send_email(subject: str, recipients: list, body: str):
    for email_addr in recipients:
        send_brevo_email(email_addr, "User", subject, body)

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    pass