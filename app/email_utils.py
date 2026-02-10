import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = "leelanjans828@gmail.com" 
SENDER_NAME = "ProLearn Admin"

def send_brevo_email(to_email: str, to_name: str, subject: str, html_content: str):
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
        print(f"❌ Error sending email: {e}")

async def send_welcome_email(email: str, name: str):
    html = f"<h1>Welcome {name}!</h1><p>You can login now.</p>"
    send_brevo_email(email, name, "Welcome to ProLearn", html)

async def send_login_alert(email: str, name: str):
    html = f"<p>New login detected for {name}.</p>"
    send_brevo_email(email, name, "Login Alert", html)

async def send_verification_email(email: str, token: str):
    pass 
async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    pass