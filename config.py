import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///prov_portal.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # SendGrid Configuration
    SMTP_SERVER = "smtp.sendgrid.net"
    SMTP_PORT = 587
    SMTP_USERNAME = "apikey"  # SendGrid requires this exact username
    SMTP_PASSWORD = os.getenv("SENDGRID_API_KEY")  # Get from environment variable
    
    # Email Configuration
    CDX_EMAIL = os.getenv("CDX_EMAIL") 