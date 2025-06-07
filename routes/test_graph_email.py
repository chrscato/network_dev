# routes/test_graph_email.py
from flask import Blueprint, jsonify, request, render_template
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Create the blueprint
test_graph_email_bp = Blueprint("test_graph_email", __name__, url_prefix="/api/test-graph-email")

@test_graph_email_bp.route("/send", methods=["GET"])
def send_test_email():
    """Test endpoint for Microsoft Graph API email integration."""
    
    # Import here to avoid circular imports
    from utils.mailers.mail_service import send_email, get_email_system_info
    
    # Get recipient from query parameter or use admin email as default
    recipient = request.args.get('recipient', os.getenv("ADMIN_EMAIL"))
    
    if not recipient:
        return jsonify({
            "status": "error", 
            "message": "No recipient specified and no ADMIN_EMAIL configured"
        }), 400
    
    # Create a test email
    subject = "🚀 Test Email from Provider Portal"
    body = """
    <html>
    <body>
        <h1>Hello from your Flask Provider Portal!</h1>
        <p>If you're reading this, the email system is working properly.</p>
        <p>This is a test message sent at: <strong>{current_time}</strong></p>
    </body>
    </html>
    """.format(current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Send the email
    try:
        # Get email system info
        email_system = get_email_system_info()
        
        # Send the test email
        result = send_email(
            subject=subject,
            body=body,
            recipient=recipient
        )
        
        # Enhanced response with more details
        response_data = {
            "status": result.get("status"),
            "message": result.get("message"),
            "time": datetime.now().isoformat(),
            "email_system": email_system["system"],
            "details": {
                "recipient": recipient,
                "subject": subject,
                "sender": os.getenv("MS_GRAPH_USER_EMAIL") or os.getenv("GMAIL_USER", "Unknown")
            }
        }
        
        # Include error details if there were any
        if result.get("status") == "error" and "details" in result:
            response_data["error_details"] = result["details"]
            
        return jsonify(response_data)
    except Exception as e:
        logger.exception("Error sending test email")
        return jsonify({
            "status": "error", 
            "message": f"Failed to send email: {str(e)}"
        }), 500

@test_graph_email_bp.route("/status", methods=["GET"])
def check_status():
    """Check if Microsoft Graph API configuration is available."""
    
    # Check for required environment variables
    required_vars = [
        "MS_GRAPH_CLIENT_ID", 
        "MS_GRAPH_CLIENT_SECRET", 
        "MS_GRAPH_TENANT_ID", 
        "MS_GRAPH_USER_EMAIL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        return jsonify({
            "status": "not_configured",
            "message": "Microsoft Graph API is not fully configured",
            "missing_variables": missing_vars
        }), 400
    
    return jsonify({
        "status": "configured",
        "sender_email": os.getenv("MS_GRAPH_USER_EMAIL"),
        "message": "Microsoft Graph API configuration is available"
    })

@test_graph_email_bp.route("/system-info")
def email_system_info():
    """Get information about the email system being used."""
    from utils.mailers.mail_service import get_email_system_info
    
    info = get_email_system_info()
    
    # Add environment variable status (without revealing sensitive values)
    graph_vars = ["MS_GRAPH_CLIENT_ID", "MS_GRAPH_CLIENT_SECRET", "MS_GRAPH_TENANT_ID", "MS_GRAPH_USER_EMAIL"]
    gmail_vars = ["GMAIL_USER", "GMAIL_PASS"]
    
    env_status = {
        "graph_api": {var: "set" if os.getenv(var) else "missing" for var in graph_vars},
        "gmail": {var: "set" if os.getenv(var) else "missing" for var in gmail_vars}
    }
    
    return jsonify({
        "email_system": info["system"],
        "timestamp": info["timestamp"],
        "environment_status": env_status,
        "current_time": datetime.now().isoformat()
    })

@test_graph_email_bp.route("/test-form")
def test_email_form():
    """Render a test form for sending emails."""
    return render_template("test_email.html")