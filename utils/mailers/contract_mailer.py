from .mail_service import send_email_with_file_attachments, get_email_system_info
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def send_contract_email(provider, contact, contract_docx_path, contract_pdf_path=None):
    """
    Send a contract email to a provider contact with the contract files attached.
    
    Args:
        provider (object): Provider object from database
        contact (object): Contact object from database
        contract_docx_path (str): Path to the contract DOCX file
        contract_pdf_path (str, optional): Path to the contract PDF file. Defaults to None.
    
    Returns:
        dict: Response from the send_email function
    """
    # Log which email system we're using
    email_system = get_email_system_info()
    logger.info(f"Sending contract email using: {email_system['system']}")
    
    # Get sender display name from environment variable or use default
    sender_name = os.getenv("CONTRACT_SENDER_NAME", "Provider Network Team")
    company_name = os.getenv("COMPANY_NAME", "Clarity Diagnostics")
    
    # Determine which files to attach
    attachments = [contract_docx_path]
    
    if contract_pdf_path and os.path.exists(contract_pdf_path):
        attachments.append(contract_pdf_path)
    
    # Format the current date
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Prepare email subject
    subject = f"Provider Agreement for {provider.name} - {current_date}"
    
    # Determine greeting based on contact information
    greeting = f"Dear {contact.name},"
    if not contact.name:
        greeting = "Hello,"
    
    # Build email body with HTML formatting
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <p>{greeting}</p>
        
        <p>I hope this email finds you well. Attached please find the provider agreement for {provider.name} 
        with {company_name}.</p>
        
        <p>The agreement includes the following key details:</p>
        <ul>
            <li><strong>Provider Name:</strong> {provider.name}</li>
            <li><strong>DBA Name:</strong> {provider.dba_name or "N/A"}</li>
            <li><strong>States Covered:</strong> {provider.states_in_contract or "N/A"}</li>
            <li><strong>Reimbursement Type:</strong> {provider.rate_type or "Standard"}</li>
        </ul>
        
        <p>Please review the attached agreement and let us know if you have any questions or concerns. 
        If everything looks good, please sign and return the agreement at your earliest convenience.</p>
        
        <p>We look forward to working with you.</p>
        
        <p>Best regards,<br>
        {sender_name}<br>
        {company_name} Provider Network Team</p>
    </body>
    </html>
    """
    
    # Determine recipient email
    recipient_email = contact.email
    
    logger.debug(f"Preparing to send contract email to {recipient_email}")
    
    # Send the email with attachments
    return send_email_with_file_attachments(
        subject=subject,
        body=body,
        recipient=recipient_email,
        file_paths=attachments,
        importance="normal"
    )

def send_contract_notification(provider, docx_path, pdf_path=None, admin_email=None):
    """
    Send a notification email to admin about contract generation.
    
    Args:
        provider (object): Provider object from database
        docx_path (str): Path to the contract DOCX file
        pdf_path (str, optional): Path to the contract PDF file. Defaults to None.
        admin_email (str, optional): Admin email to send notification to. If None, uses env var.
    
    Returns:
        dict: Response from the send_email function
    """
    # Log which email system we're using
    email_system = get_email_system_info()
    logger.info(f"Sending contract notification using: {email_system['system']}")
    
    # Get admin email from param or environment variable
    recipient = admin_email or os.getenv("ADMIN_EMAIL")
    if not recipient:
        logger.warning("No admin email provided or configured for notification")
        return {"status": "error", "message": "No admin email provided or configured"}
    
    # Get company name from environment variable or use default
    company_name = os.getenv("COMPANY_NAME", "Clarity Diagnostics")
    
    # Build email subject
    subject = f"[NOTIFICATION] Contract Generated for {provider.name}"
    
    # Build the file status information
    file_status = []
    
    if docx_path and os.path.exists(docx_path):
        file_size = os.path.getsize(docx_path) / 1024  # Size in KB
        file_status.append(f"DOCX File: Available ({file_size:.1f} KB)")
    else:
        file_status.append("DOCX File: Not available or missing")
    
    if pdf_path and os.path.exists(pdf_path):
        file_size = os.path.getsize(pdf_path) / 1024  # Size in KB
        file_status.append(f"PDF File: Available ({file_size:.1f} KB)")
    else:
        file_status.append("PDF File: Not available or missing")
    
    # Build email body
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Contract Generation Notification</h2>
        
        <p>A new provider contract has been generated in the system.</p>
        
        <h3>Provider Details:</h3>
        <ul>
            <li><strong>Provider Name:</strong> {provider.name}</li>
            <li><strong>DBA Name:</strong> {provider.dba_name or "N/A"}</li>
            <li><strong>Provider Type:</strong> {provider.provider_type or "N/A"}</li>
            <li><strong>NPI:</strong> {provider.npi or "N/A"}</li>
            <li><strong>Specialty:</strong> {provider.specialty or "N/A"}</li>
            <li><strong>States:</strong> {provider.states_in_contract or "N/A"}</li>
            <li><strong>Rate Type:</strong> {provider.rate_type or "Standard"}</li>
        </ul>
        
        <h3>File Status:</h3>
        <ul>
            <li>{file_status[0]}</li>
            <li>{file_status[1]}</li>
        </ul>
        
        <p>This contract is now ready for review and can be sent to the provider.</p>
        
        <p>This is an automated notification from the {company_name} Provider Portal.</p>
    </body>
    </html>
    """
    
    # Send email without attachments (just notification)
    return send_email_with_file_attachments(
        subject=subject,
        body=body,
        recipient=recipient
    )