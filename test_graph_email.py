import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Import our MS Graph email module
from utils.mailers.graph_emailer import send_email, send_email_with_file_attachments

def test_graph_email():
    """Test the Microsoft Graph API email integration."""
    
    # Check if required environment variables are set
    required_vars = [
        "MS_GRAPH_CLIENT_ID", 
        "MS_GRAPH_CLIENT_SECRET", 
        "MS_GRAPH_TENANT_ID", 
        "MS_GRAPH_USER_EMAIL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease set these variables in your .env file.")
        return False
    
    # Get test recipient
    recipient = os.getenv("ADMIN_EMAIL")
    if not recipient:
        recipient = input("Enter a recipient email address for testing: ")
        if not recipient:
            print("Error: No recipient email provided.")
            return False
    
    print(f"Sending test email to: {recipient}")
    print(f"Using sender: {os.getenv('MS_GRAPH_USER_EMAIL')}")
    
    # Create a test email
    subject = "🚀 Test Email from Microsoft Graph API"
    body = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h1>Hello from the Provider Portal Test Script!</h1>
        
        <p>If you're reading this, the Microsoft Graph API email integration is working properly.</p>
        
        <p>This email was sent using the following configuration:</p>
        <ul>
            <li><strong>Client ID:</strong> [HIDDEN]</li>
            <li><strong>Tenant ID:</strong> [HIDDEN]</li>
            <li><strong>Sender:</strong> {sender}</li>
        </ul>
        
        <p>You can now use the Microsoft Graph API to send emails from your Flask application.</p>
    </body>
    </html>
    """.format(sender=os.getenv('MS_GRAPH_USER_EMAIL'))
    
    # Send the email
    try:
        print("Sending email...")
        result = send_email(
            subject=subject,
            body=body,
            recipient=recipient
        )
        
        print(f"Result: {result['status']}")
        
        if result['status'] == 'success':
            print("✅ Email sent successfully!")
            return True
        else:
            print(f"❌ Email failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception while sending email: {str(e)}")
        return False

def test_email_with_attachment():
    """Test the Microsoft Graph API email with attachment."""
    
    # Check if required environment variables are set
    if not all([
        os.getenv("MS_GRAPH_CLIENT_ID"),
        os.getenv("MS_GRAPH_CLIENT_SECRET"),
        os.getenv("MS_GRAPH_TENANT_ID"),
        os.getenv("MS_GRAPH_USER_EMAIL")
    ]):
        print("Error: Microsoft Graph API environment variables not configured.")
        return False
    
    # Get test recipient
    recipient = os.getenv("ADMIN_EMAIL")
    if not recipient:
        recipient = input("Enter a recipient email address for testing: ")
        if not recipient:
            print("Error: No recipient email provided.")
            return False
    
    # Create test file if it doesn't exist
    test_file_path = "test_attachment.txt"
    if not os.path.exists(test_file_path):
        with open(test_file_path, "w") as f:
            f.write("This is a test attachment file.")
    
    print(f"Sending test email with attachment to: {recipient}")
    
    # Send email with attachment
    try:
        print("Sending email with attachment...")
        result = send_email_with_file_attachments(
            subject="Test Email with Attachment",
            body="<h1>This email includes an attachment</h1><p>Please check the attached file.</p>",
            recipient=recipient,
            file_paths=[test_file_path]
        )
        
        print(f"Result: {result['status']}")
        
        if result['status'] == 'success':
            print("✅ Email with attachment sent successfully!")
            return True
        else:
            print(f"❌ Email with attachment failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception while sending email with attachment: {str(e)}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    print("=== Testing Microsoft Graph API Email Integration ===\n")
    
    # Test basic email
    print("\n1. Testing basic email functionality...")
    test_graph_email()
    
    # Test email with attachment
    print("\n2. Testing email with attachment...")
    test_email_with_attachment()