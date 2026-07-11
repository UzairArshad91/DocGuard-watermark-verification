import resend
import os

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_email_alert(reason, user_id, doc_id, filename="unknown"):
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "ea16826@gmail.com",
        "subject": "Tamper Alert",
        "text": f"Alert: {reason} | User: {user_id} | Doc: {filename}"
    })