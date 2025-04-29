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
from utils.generate_contract import generate_contract

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-key'

# Initialize the database
db.init_app(app)

def test_contract_generation():
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create a test provider with just the essential fields
        provider = Provider(
            id=str(uuid.uuid4()),
            name="Test Provider Name",  # This will replace {{provider_name}}
            states_in_contract="CA,NV"  # This will be used for the rates table
        )
        
        # Add to database
        db.session.add(provider)
        db.session.commit()
        
        try:
            # Generate contract
            docx_path, pdf_path = generate_contract(provider.id)
            print(f"Contract generated successfully!")
            print(f"DOCX: {docx_path}")
            print(f"PDF: {pdf_path}")
        except Exception as e:
            print(f"Error generating contract: {e}")
        finally:
            # Clean up
            db.session.delete(provider)
            db.session.commit()
            
            # Remove test database
            if os.path.exists('test.db'):
                os.remove('test.db')

if __name__ == '__main__':
    test_contract_generation() 