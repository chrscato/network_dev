import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

app = Flask(__name__)

@app.route('/send-test-email', methods=['GET'])
def send_test_email():
    subject = "🚀 Test Email from Flask API"
    body = """
    Hello from your Flask test endpoint!

    If you're reading this, the email system is working properly.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        return jsonify({"status": "✅ Email sent!"})
    except Exception as e:
        return jsonify({"status": "❌ Failed", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
