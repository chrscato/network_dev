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
    
    # New tracking fields
    message_id = db.Column(db.String(255))       # Individual message ID
    conversation_id = db.Column(db.String(255))  # Outlook conversation ID
    
    def __repr__(self):
        return f"<Outreach {self.id}>"
    
    def update_email_tracking(self, message_id, conversation_id):
        """Helper method to update email tracking info."""
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.status = 'sent'
        db.session.commit()
    
    def has_tracking_info(self):
        """Check if this outreach has email tracking info."""
        return bool(self.message_id and self.conversation_id) 