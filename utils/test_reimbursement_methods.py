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
from utils.generate_contract import generate_contract, IMAGING_CATEGORIES

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-key'

# Initialize the database
db.init_app(app)

def test_reimbursement_methods():
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create a test provider
        provider = Provider(
            id=str(uuid.uuid4()),
            name="Test Provider",
            dba_name="Test DBA",
            address="123 Test St, Test City, CA 12345",
            provider_type="Imaging Center",
            states_in_contract="CA,NV",
            npi="1234567890",
            specialty="Diagnostic Imaging",
            rate_type="standard",
            wcfs_percentage=85,
            status="active"
        )
        
        # Add to database
        db.session.add(provider)
        db.session.commit()
        
        print(f"Created test provider with ID: {provider.id}")
        
        # Test 1: Standard rate per imaging category
        print("\n=== Testing Standard Rate Method ===")
        try:
            docx_path, pdf_path = generate_contract(provider.id, method='standard')
            print(f"Contract generated successfully with standard rates!")
            print(f"DOCX: {docx_path}")
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract with standard rates: {e}")
        
        # Test 2: % of WCFS
        print("\n=== Testing WCFS Percentage Method ===")
        # Create WCFS percentages for each category
        wcfs_percentages = {
            "MRI w/o": 80,
            "MRI w/": 85,
            "MRI w/ & w/o": 90,
            "CT w/o": 75,
            "CT w/": 80,
            "CT w/ & w/o": 85,
            "XRAY": 70,
            "Arthrograms": 95
        }
        
        try:
            docx_path, pdf_path = generate_contract(provider.id, method='wcfs', wcfs_percentages=wcfs_percentages)
            print(f"Contract generated successfully with WCFS percentages!")
            print(f"DOCX: {docx_path}")
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract with WCFS percentages: {e}")
        
        # Test 3: Custom rate per category
        print("\n=== Testing Custom Rate Method ===")
        # Create custom rates for each category
        custom_rates = {
            "MRI w/o": 350,
            "MRI w/": 450,
            "MRI w/ & w/o": 500,
            "CT w/o": 250,
            "CT w/": 325,
            "CT w/ & w/o": 400,
            "XRAY": 30,
            "Arthrograms": 650
        }
        
        try:
            docx_path, pdf_path = generate_contract(provider.id, method='custom', custom_rates=custom_rates)
            print(f"Contract generated successfully with custom rates!")
            print(f"DOCX: {docx_path}")
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract with custom rates: {e}")
        
        # Clean up
        db.session.delete(provider)
        db.session.commit()
        
        # Remove test database
        if os.path.exists('test.db'):
            os.remove('test.db')

if __name__ == "__main__":
    test_reimbursement_methods() 