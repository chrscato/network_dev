from models import db
import uuid
from datetime import datetime
import json
import os

class Provider(db.Model):
    __tablename__ = 'providers'
    
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(128), nullable=False)
    dba_name = db.Column(db.String(128))
    address = db.Column(db.String(256))
    provider_type = db.Column(db.String(50))  # imaging, EMG, etc.
    states_in_contract = db.Column(db.String(256))  # comma-separated
    rate_type = db.Column(db.String(50))  # 'standard' or 'wcfs'
    wcfs_percentages = db.Column(db.Text)  # JSON string of category -> percentage
    npi = db.Column(db.String(20))
    specialty = db.Column(db.String(128))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contract file paths
    contract_docx = db.Column(db.String(256))
    contract_pdf = db.Column(db.String(256))

    # Define the relationship with Contact model
    contacts = db.relationship('Contact', backref='provider', lazy=True, cascade="all, delete-orphan")
    outreach = db.relationship('Outreach', backref='provider', lazy=True)

    @property
    def wcfs_percentages_dict(self):
        if self.wcfs_percentages:
            return json.loads(self.wcfs_percentages)
        return {}

    @wcfs_percentages_dict.setter
    def wcfs_percentages_dict(self, value):
        if value:
            self.wcfs_percentages = json.dumps(value)
        else:
            self.wcfs_percentages = None

    def has_contract_docx(self):
        return self.contract_docx and os.path.exists(self.contract_docx)
    
    def has_contract_pdf(self):
        return self.contract_pdf and os.path.exists(self.contract_pdf)

    def __repr__(self):
        return f"<Provider {self.name}>" 