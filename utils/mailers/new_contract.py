import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_new_provider_email(provider_info: dict) -> bool:
    """
    Sends a structured email for a new provider to trigger Power Automate.

    Args:
        provider_info (dict): Must include:
            - uuid
            - name
            - facility
            - specialty
            - email
            - phone
            - contract_link (optional)

    Returns:
        bool: True if sent successfully, False otherwise
    """
    # Load env vars
    GMAIL_USER = os.getenv("GMAIL_USER")
    GMAIL_PASS = os.getenv("GMAIL_PASS")
    RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

    # Prepare email
    subject = f"New Provider: {provider_info.get('name')} | UUID: {provider_info.get('uuid')}"
    
    body = f"""New Provider Details

UUID: {provider_info.get('uuid')}
Provider Name: {provider_info.get('name')}
Facility: {provider_info.get('facility')}
Specialty: {provider_info.get('specialty')}
Email: {provider_info.get('email')}
Phone: {provider_info.get('phone')}
Contract Link: {provider_info.get('contract_link', 'N/A')}

Instructions:
Please review the attached contract. If everything looks good, reply directly to this email.

Thank you,
The Network Team
"""

    try:
        # Create email
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"] = RECIPIENT_EMAIL
        msg.attach(MIMEText(body, "plain"))

        # Send email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()

        print(f"✅ Email sent for provider {provider_info.get('name')}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
