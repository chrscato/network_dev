from models import db
from datetime import datetime
import uuid

class Intake(db.Model):
    __tablename__ = 'intakes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = db.Column(db.String(36), db.ForeignKey('providers.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., 'initial', 'follow_up', 'contract'
    status = db.Column(db.String(50), nullable=False, default='pending')  # e.g., 'pending', 'completed', 'cancelled'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = db.relationship('Provider', backref=db.backref('intakes', lazy=True))
    contact = db.relationship('Contact', backref=db.backref('intakes', lazy=True))
    
    def __init__(self, provider_id, contact_id=None, type='initial', status='pending', notes=None):
        self.id = str(uuid.uuid4())
        self.provider_id = provider_id
        self.contact_id = contact_id
        self.type = type
        self.status = status
        self.notes = notes
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Intake {self.id}: {self.type} for Provider {self.provider_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'provider_id': self.provider_id,
            'contact_id': self.contact_id,
            'type': self.type,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 