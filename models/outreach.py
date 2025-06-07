from models import db
import uuid
from datetime import datetime

class Outreach(db.Model):
    __tablename__ = 'outreach'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = db.Column(db.String, db.ForeignKey('providers.id'), nullable=False)
    contact_id = db.Column(db.String, db.ForeignKey('contacts.id'))
    type = db.Column(db.String(50))  # cold, follow-up, etc.
    method = db.Column(db.String(50))  # email, phone, etc.
    notes = db.Column(db.Text)
    status = db.Column(db.String(50))  # pending, completed, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    contract_id = db.Column(db.Text)
    
    # Email tracking fields
    message_id = db.Column(db.String(255))       # Individual message ID
    conversation_id = db.Column(db.String(255))  # Outlook conversation ID
    
    # Reply tracking fields (matching your database schema)
    last_reply_date = db.Column(db.DateTime)
    reply_preview = db.Column(db.Text)
    reply_sender_email = db.Column(db.String(128))
    reply_status = db.Column(db.String(20), default='none')  # none, unread, read, responded
    reply_received = db.Column(db.Boolean, default=False)
    reply_count = db.Column(db.Integer, default=0)

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
    
    # Reply tracking methods
    def mark_reply_received(self, sender_email, reply_preview_text, reply_date=None):
        """Mark that a reply was received and store preview."""
        self.reply_received = True
        self.reply_count = (self.reply_count or 0) + 1
        self.last_reply_date = reply_date or datetime.utcnow()
        self.reply_sender_email = sender_email
        self.reply_status = 'unread'
        
        # Store first 200 characters as preview
        if reply_preview_text:
            self.reply_preview = reply_preview_text[:200]
            if len(reply_preview_text) > 200:
                self.reply_preview += "..."
        
        # Update notes with reply info
        reply_note = f"\n\nReply received from {sender_email} on {self.last_reply_date.strftime('%Y-%m-%d %H:%M')}"
        self.notes = (self.notes or "") + reply_note
        
        db.session.commit()
    
    def mark_reply_read(self):
        """Mark reply as read."""
        if self.reply_received and self.reply_status == 'unread':
            self.reply_status = 'read'
            db.session.commit()
    
    def mark_reply_responded(self):
        """Mark that we've responded to the reply."""
        if self.reply_received:
            self.reply_status = 'responded'
            db.session.commit()
    
    def get_reply_indicator_class(self):
        """Get CSS class for reply status indicator."""
        if not self.reply_received:
            return 'no-reply'
        elif self.reply_status == 'unread':
            return 'reply-unread'
        elif self.reply_status == 'read':
            return 'reply-read'
        elif self.reply_status == 'responded':
            return 'reply-responded'
        return 'no-reply'
    
    def get_reply_status_text(self):
        """Get human-readable reply status."""
        if not self.reply_received:
            return 'No reply'
        elif self.reply_status == 'unread':
            return f'New reply ({self.reply_count})'
        elif self.reply_status == 'read':
            return f'Reply read ({self.reply_count})'
        elif self.reply_status == 'responded':
            return f'Replied ({self.reply_count})'
        return 'No reply' 