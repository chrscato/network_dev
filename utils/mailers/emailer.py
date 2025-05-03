import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app
import os
import logging

def send_email(to_email, subject, body, attachments=None):
    """
    Send an email with optional attachments.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (JSON string)
        attachments (list): List of attachment dictionaries with 'filename', 'path', and 'mime_type'
    """
    try:
        # Get SMTP configuration from app settings
        smtp_server = current_app.config['SMTP_SERVER']
        smtp_port = current_app.config['SMTP_PORT']
        smtp_username = current_app.config['SMTP_USERNAME']
        smtp_password = current_app.config['SMTP_PASSWORD']
        from_email = current_app.config['SMTP_USERNAME']
        
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            raise ValueError("SMTP configuration is incomplete")
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                try:
                    file_path = os.path.join(current_app.root_path, attachment['path'])
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=attachment['filename'])
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
                    logging.info(f"Successfully attached {attachment['filename']}")
                except Exception as e:
                    logging.error(f"Error attaching {attachment['filename']}: {str(e)}")
                    continue
        
        # Connect to SMTP server and send email
        logging.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            logging.info("Starting TLS connection")
            server.login(smtp_username, smtp_password)
            logging.info("Successfully logged in to SMTP server")
            server.send_message(msg)
            logging.info(f"Email sent successfully to {to_email}")
        
        return True
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        raise
