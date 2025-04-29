from models import db
import uuid
from datetime import datetime

class StandardRates(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    state = db.Column(db.String(2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create a unique constraint on state and category
    __table_args__ = (db.UniqueConstraint('state', 'category', name='uix_state_category'),)
    
    def __repr__(self):
        return f"<StandardRates {self.state} {self.category}: ${self.rate}>" 