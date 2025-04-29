import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from models import db
from models.provider import Provider
from utils.generate_contract import generate_contract

def test_contract_generation():
    with app.app_context():
        # Create a test provider
        provider = Provider(
            id=str(uuid.uuid4()),
            name="Test Imaging Center",
            dba_name="TIC Medical Group",
            address="123 Test St, Los Angeles, CA 90001",
            provider_type="Imaging",
            states_in_contract="CA, NY, TX",
            npi="1234567890",
            specialty="Radiology",
            rate_type="wcfs",
            wcfs_percentage=80.0,
            status="active"
        )
        
        # Add to database
        db.session.add(provider)
        db.session.commit()
        
        print(f"Created test provider with ID: {provider.id}")
        
        # Generate contract
        try:
            docx_path, pdf_path = generate_contract(provider.id)
            print(f"Contract generated successfully!")
            print(f"DOCX path: {docx_path}")
            print(f"PDF path: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract: {e}")

if __name__ == "__main__":
    test_contract_generation() 