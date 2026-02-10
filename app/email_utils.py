async def send_email(subject: str, recipients: list, body: str):
    print(f"📧 [Mock Email] To: {recipients} | Subject: {subject}")
    pass

async def send_verification_email(email: str, token: str):
    print(f"📧 [Mock Verify] To: {email} | Token: {token}")
    pass

async def send_welcome_email(email: str, name: str):
    print(f"📧 [Mock Welcome] To: {email}")
    pass

async def send_login_alert(email: str, name: str):
    pass

async def send_enrollment_confirm(email: str, name: str, course_title: str, teacher_name: str, price: float):
    print(f"📧 [Mock Enrollment] To: {email} | Course: {course_title}")
    pass

async def send_teacher_assigned_email(email: str, teacher_name: str, course_title: str):
    pass 