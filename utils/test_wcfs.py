import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach
from models.standard_rates import StandardRates
from utils.generate_contract import generate_contract

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-key'

# Initialize the database
db.init_app(app)

def test_wcfs_method():
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create a test provider
        provider = Provider(
            id=str(uuid.uuid4()),
            name="WCFS Test Provider",
            dba_name="WCFS Medical Imaging",
            address="456 WCFS St, Test City, CA 12345",
            provider_type="Imaging Center",
            states_in_contract="CA,NV",
            npi="9876543210",
            specialty="Diagnostic Imaging",
            rate_type="wcfs",
            wcfs_percentage=85,
            status="active"
        )
        
        # Add to database
        db.session.add(provider)
        db.session.commit()
        
        print(f"\nCreated test provider with ID: {provider.id}")
        
        # Test WCFS percentages
        print("\n=== Testing WCFS Percentage Method ===")
        # Create different WCFS percentages for each category
        wcfs_percentages = {
            "MRI w/o": 85,
            "MRI w/": 80,
            "MRI w/ & w/o": 75,
            "CT w/o": 90,
            "CT w/": 85,
            "CT w/ & w/o": 80,
            "XRAY": 95,
            "Arthrograms": 70
        }
        
        print("\nWCFS percentages that should appear in contract:")
        for category, percentage in wcfs_percentages.items():
            print(f"{category}: {percentage}% of WCFS")
        
        try:
            docx_path, pdf_path = generate_contract(provider.id, method='wcfs', wcfs_percentages=wcfs_percentages)
            print(f"\nContract generated successfully!")
            print(f"DOCX: {docx_path}")
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"\nError generating contract: {e}")
        
        # Clean up
        db.session.delete(provider)
        db.session.commit()
        
        # Remove test database
        if os.path.exists('test.db'):
            os.remove('test.db')

if __name__ == "__main__":
    test_wcfs_method() 