import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from flask import current_app
import os
import logging
import socket

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body, attachments=None):
    """
    Send an email with optional attachments using SendGrid.
    
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
        from_email = "automate.cdx@gmail.com"  # Your verified sender email
        
        logger.debug(f"SMTP Configuration - Server: {smtp_server}, Port: {smtp_port}, Username: {smtp_username}")
        logger.debug(f"SMTP Password length: {len(smtp_password) if smtp_password else 0}")
        
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            missing = []
            if not smtp_server: missing.append('SMTP_SERVER')
            if not smtp_port: missing.append('SMTP_PORT')
            if not smtp_username: missing.append('SMTP_USERNAME')
            if not smtp_password: missing.append('SMTP_PASSWORD')
            raise ValueError(f"SMTP configuration is incomplete. Missing: {', '.join(missing)}")
        
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
                    logger.debug(f"Attempting to attach file: {file_path}")
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=attachment['filename'])
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
                    logger.info(f"Successfully attached {attachment['filename']}")
                except Exception as e:
                    logger.error(f"Error attaching {attachment['filename']}: {str(e)}")
                    continue
        
        # Connect to SMTP server and send email
        logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
        try:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            logger.debug("SMTP connection established")
            
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            logger.debug("TLS started")
            
            logger.debug("Attempting SMTP login...")
            server.login(smtp_username, smtp_password)
            logger.debug("SMTP login successful")
            
            server.send_message(msg)
            logger.info(f"Email sent successfully to {to_email}")
            
            server.quit()
            logger.debug("SMTP connection closed")
            
        except socket.timeout:
            logger.error("SMTP connection timed out")
            raise
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            raise
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        raise
