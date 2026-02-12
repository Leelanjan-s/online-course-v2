import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "leelanjans828@gmail.com" 
SENDER_NAME = "ProLearn Admin"

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
            print(f"✅ Email sent successfully to {to_email}")
        else:
            print(f"❌ Brevo Error: {response.status_code} - {response.text}") 
    except Exception as e:
        print(f"❌ Network Error: {e}")

async def send_verification_email(email: str, token: str):
    link = f"https://online-course-v2-production.up.railway.app/auth/verify/{token}"
    html = f"<h1>Verify Account</h1><p>Please verify your email to access ProLearn.</p><a href='{link}' style='background:blue;color:white;padding:10px;text-decoration:none;'>Verify Now</a>"
    send_brevo_email(email, "New User", "Verify Your Email", html)

async def send_welcome_email(email: str, name: str):
    send_brevo_email(email, name, "Welcome to ProLearn", f"<h1>Welcome {name}!</h1><p>Your account is active.</p>")

async def send_login_alert(email: str, name: str):
    send_brevo_email(email, name, "Login Alert", f"<p>Hello {name}, we detected a new login to your account.</p>")

async def send_enrollment_confirm(email: str, name: str, course_title: str):
    # ✅ FIX: This sends the email when Stripe payment succeeds
    html = f"<h1>Enrollment Successful!</h1><p>Hi {name}, you have successfully enrolled in <b>{course_title}</b>. Happy Learning!</p>"
    send_brevo_email(email, name, f"Enrolled: {course_title}", html)

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    # ✅ FIX: Filled in the empty function
    html = f"<h1>New Course Assigned</h1><p>Hello {teacher_name}, you have been assigned as the instructor for the course: <b>{course_title}</b>.</p>"
    send_brevo_email(email, teacher_name, "Course Assignment", html)