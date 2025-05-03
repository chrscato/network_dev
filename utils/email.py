import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def send_email(to_email, subject, body):
    """
    Send an email using the configured SMTP settings.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body content
    """
    # Get email configuration from app config
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_username = current_app.config.get('SMTP_USERNAME')
    smtp_password = current_app.config.get('SMTP_PASSWORD')
    from_email = current_app.config.get('FROM_EMAIL', smtp_username)
    
    if not all([smtp_username, smtp_password]):
        raise ValueError("SMTP credentials not configured")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add body
    msg.attach(MIMEText(body, 'plain'))
    
    # Create SMTP connection
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    
    # Login and send email
    server.login(smtp_username, smtp_password)
    server.send_message(msg)
    server.quit() 