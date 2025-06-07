import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Determine which email system to use
use_graph_api = all([
    os.getenv("MS_GRAPH_CLIENT_ID"),
    os.getenv("MS_GRAPH_CLIENT_SECRET"),
    os.getenv("MS_GRAPH_TENANT_ID"),
    os.getenv("MS_GRAPH_USER_EMAIL")
])

if use_graph_api:
    logger.info("Using Microsoft Graph API for emails")
    try:
        from .graph_emailer import send_email, send_email_with_file_attachments
        EMAIL_SYSTEM = "Microsoft Graph API"
    except ImportError as e:
        logger.error(f"Failed to import Graph API mailer: {e}")
        use_graph_api = False
else:
    logger.warning("Microsoft Graph API not configured with environment variables")

if not use_graph_api:
    logger.info("Using Gmail SMTP for emails")
    try:
        from .emailer import send_email as gmail_send_email
        EMAIL_SYSTEM = "Gmail SMTP"
        
        # Create compatible function signatures for Gmail
        def send_email(subject, body, recipient, importance=None, cc=None, bcc=None, reply_to=None, attachments=None):
            logger.info(f"Sending email via Gmail SMTP to {recipient}")
            return gmail_send_email(subject, body, recipient)
        
        def send_email_with_file_attachments(subject, body, recipient, file_paths=None, **kwargs):
            logger.info(f"Sending email with attachments via Gmail SMTP to {recipient}")
            # This assumes your Gmail implementation can handle attachments
            # If it doesn't, you'll need to implement attachment handling here
            
            # For now, just pass through to the simple send_email function
            return gmail_send_email(subject, body, recipient)
            
    except ImportError as e:
        logger.error(f"Failed to import Gmail mailer: {e}")
        raise ImportError("No email module available")

def get_email_system_info():
    """Return information about the current email system."""
    return {
        "system": EMAIL_SYSTEM,
        "timestamp": datetime.now().isoformat(),
        "environment_variables": {
            "graph_api_configured": use_graph_api,
            "missing_vars": [var for var in ["MS_GRAPH_CLIENT_ID", "MS_GRAPH_CLIENT_SECRET", "MS_GRAPH_TENANT_ID", "MS_GRAPH_USER_EMAIL"] 
                            if not os.getenv(var)]
        }
    }