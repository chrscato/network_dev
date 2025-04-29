import os
import sys
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db
from models.standard_rates import StandardRates

# Create a minimal Flask app for testing
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test-key'

# Initialize the database
db.init_app(app)

# Standard rates for different states and categories
STANDARD_RATES_DATA = [
    # California rates
    {"state": "CA", "category": "MRI w/o", "rate": 300},
    {"state": "CA", "category": "MRI w/", "rate": 400},
    {"state": "CA", "category": "MRI w/ & w/o", "rate": 450},
    {"state": "CA", "category": "CT w/o", "rate": 200},
    {"state": "CA", "category": "CT w/", "rate": 275},
    {"state": "CA", "category": "CT w/ & w/o", "rate": 350},
    {"state": "CA", "category": "XRAY", "rate": 25},
    {"state": "CA", "category": "Arthrograms", "rate": 570},
    
    # Nevada rates
    {"state": "NV", "category": "MRI w/o", "rate": 325},
    {"state": "NV", "category": "MRI w/", "rate": 425},
    {"state": "NV", "category": "MRI w/ & w/o", "rate": 475},
    {"state": "NV", "category": "CT w/o", "rate": 225},
    {"state": "NV", "category": "CT w/", "rate": 300},
    {"state": "NV", "category": "CT w/ & w/o", "rate": 375},
    {"state": "NV", "category": "XRAY", "rate": 30},
    {"state": "NV", "category": "Arthrograms", "rate": 600},
    
    # Texas rates
    {"state": "TX", "category": "MRI w/o", "rate": 275},
    {"state": "TX", "category": "MRI w/", "rate": 375},
    {"state": "TX", "category": "MRI w/ & w/o", "rate": 425},
    {"state": "TX", "category": "CT w/o", "rate": 175},
    {"state": "TX", "category": "CT w/", "rate": 250},
    {"state": "TX", "category": "CT w/ & w/o", "rate": 325},
    {"state": "TX", "category": "XRAY", "rate": 20},
    {"state": "TX", "category": "Arthrograms", "rate": 550},
]

def populate_standard_rates():
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Check if data already exists
        if StandardRates.query.first():
            print("Standard rates already exist in the database.")
            return
        
        # Add standard rates
        for rate_data in STANDARD_RATES_DATA:
            rate = StandardRates(
                id=str(uuid.uuid4()),
                state=rate_data["state"],
                category=rate_data["category"],
                rate=rate_data["rate"]
            )
            db.session.add(rate)
        
        # Commit the changes
        db.session.commit()
        print(f"Added {len(STANDARD_RATES_DATA)} standard rates to the database.")

if __name__ == "__main__":
    populate_standard_rates() 