from models import db
import uuid
from datetime import datetime

class Outreach(db.Model):
    __tablename__ = 'outreach'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = db.Column(db.String, db.ForeignKey('providers.id'), nullable=False)
    contact_id = db.Column(db.String, db.ForeignKey('contacts.id'))
    method = db.Column(db.String(50))  # email, phone, etc.
    type = db.Column(db.String(50))  # cold, follow-up, etc.
    notes = db.Column(db.Text)
    status = db.Column(db.String(50))  # pending, completed, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Outreach {self.id}>" 