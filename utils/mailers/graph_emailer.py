import os
import requests
import msal
import json
from datetime import datetime, timedelta

# Configuration values that should be stored in environment variables
client_id = os.getenv("MS_GRAPH_CLIENT_ID")
client_secret = os.getenv("MS_GRAPH_CLIENT_SECRET")
tenant_id = os.getenv("MS_GRAPH_TENANT_ID")
user_email = os.getenv("MS_GRAPH_USER_EMAIL")  # The email account to send from

# Token cache for storing and retrieving acquired tokens
token_cache = {}

def get_access_token():
    """
    Get Microsoft Graph API access token using client credentials flow.
    Will use cached token if it's still valid.
    """
    global token_cache
    
    # Check if we have a cached token that's still valid
    if 'access_token' in token_cache and 'expires_at' in token_cache:
        # If token is still valid (with a 5-minute buffer)
        if datetime.now() < token_cache['expires_at'] - timedelta(minutes=5):
            return token_cache['access_token']
    
    # Token doesn't exist or is expired, request a new one
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=authority
    )
    
    # The scope needed for sending mail
    scopes = ["https://graph.microsoft.com/.default"]
    
    # Get token using client credentials flow
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" in result:
        # Cache token with expiration time
        token_cache['access_token'] = result['access_token']
        token_cache['expires_at'] = datetime.now() + timedelta(seconds=result['expires_in'])
        return result['access_token']
    else:
        error_message = f"Error acquiring token: {result.get('error')}: {result.get('error_description')}"
        raise Exception(error_message)

def send_email(subject, body, recipient, importance="normal", cc=None, bcc=None, reply_to=None, attachments=None):
    """
    Send an email using Microsoft Graph API.
    
    Args:
        subject (str): Email subject
        body (str): Email body content (can be HTML)
        recipient (str): Email address of the recipient
        importance (str, optional): Email importance. Defaults to "normal".
        cc (list, optional): List of CC recipients. Defaults to None.
        bcc (list, optional): List of BCC recipients. Defaults to None.
        reply_to (list, optional): Reply-to addresses. Defaults to None.
        attachments (list, optional): List of dictionaries with attachment details. Defaults to None.
            Format: [{'name': 'file.txt', 'content_type': 'text/plain', 'content': 'base64_encoded_content'}]
    
    Returns:
        dict: Response from the API call
    """
    try:
        # Get access token
        access_token = get_access_token()
        
        # Prepare the headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare recipient format
        to_recipients = [{"emailAddress": {"address": recipient}}]
        
        # Prepare CC recipients if provided
        cc_recipients = []
        if cc:
            if isinstance(cc, str):
                cc = [cc]  # Convert single email to list
            cc_recipients = [{"emailAddress": {"address": email}} for email in cc]
        
        # Prepare BCC recipients if provided
        bcc_recipients = []
        if bcc:
            if isinstance(bcc, str):
                bcc = [bcc]  # Convert single email to list
            bcc_recipients = [{"emailAddress": {"address": email}} for email in bcc]
        
        # Prepare reply-to addresses if provided
        reply_to_recipients = []
        if reply_to:
            if isinstance(reply_to, str):
                reply_to = [reply_to]  # Convert single email to list
            reply_to_recipients = [{"emailAddress": {"address": email}} for email in reply_to]
        
        # Check if the body is HTML
        is_html = "<html" in body.lower() or "<body" in body.lower()
        content_type = "html" if is_html else "text"
        
        # Build the email message
        email_message = {
            "message": {
                "subject": subject,
                "importance": importance,
                "body": {
                    "contentType": content_type,
                    "content": body
                },
                "toRecipients": to_recipients,
                "ccRecipients": cc_recipients,
                "bccRecipients": bcc_recipients
            },
            "saveToSentItems": "true"
        }
        
        # Add reply-to if specified
        if reply_to_recipients:
            email_message["message"]["replyTo"] = reply_to_recipients
        
        # Add attachments if provided
        if attachments:
            email_message["message"]["attachments"] = []
            for attachment in attachments:
                email_message["message"]["attachments"].append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": attachment["name"],
                    "contentType": attachment["content_type"],
                    "contentBytes": attachment["content"]
                })
        
        # Send the email
        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail"
        response = requests.post(endpoint, headers=headers, data=json.dumps(email_message))
        
        # Check for success
        if response.status_code == 202:  # 202 Accepted is the success status for sending email
            return {"status": "success", "message": "Email sent successfully"}
        else:
            error_detail = response.json() if response.text else {"message": "No error details available"}
            return {
                "status": "error", 
                "code": response.status_code,
                "message": f"Failed to send email: {response.reason}",
                "details": error_detail
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Exception while sending email: {str(e)}"}

def send_email_with_file_attachments(subject, body, recipient, file_paths=None, **kwargs):
    """
    Send an email with file attachments.
    
    Args:
        subject (str): Email subject
        body (str): Email body
        recipient (str): Email recipient
        file_paths (list): List of file paths to attach
        **kwargs: Additional arguments to pass to send_email
    
    Returns:
        dict: Response from the send_email function
    """
    import base64
    import mimetypes
    import os
    
    attachments = []
    
    if file_paths:
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Get file name and content type
                file_name = os.path.basename(file_path)
                content_type, _ = mimetypes.guess_type(file_path)
                
                if content_type is None:
                    # Default to binary if content type can't be determined
                    content_type = 'application/octet-stream'
                
                # Read and encode the file
                with open(file_path, 'rb') as file:
                    content = base64.b64encode(file.read()).decode('utf-8')
                
                # Add to attachments list
                attachments.append({
                    'name': file_name,
                    'content_type': content_type,
                    'content': content
                })
    
    # Send email with attachments
    return send_email(subject, body, recipient, attachments=attachments, **kwargs)

# Example usage
if __name__ == "__main__":
    # Simple test
    result = send_email(
        subject="Test Email from Microsoft Graph API",
        body="<h1>Hello!</h1><p>This is a test email sent using Microsoft Graph API.</p>",
        recipient="test@example.com"
    )
    print(result)