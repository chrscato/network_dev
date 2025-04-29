from flask import Flask
from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Create tables
    db.create_all()
    
    # Create a provider
    provider = Provider(
        id=str(uuid.uuid4()),
        name='Test Provider',
        dba_name='Test DBA',
        address='123 Test St',
        provider_type='Imaging',
        states_in_contract='CA, NY, TX',
        npi='1234567890',
        specialty='Radiology',
        status='active'
    )
    db.session.add(provider)
    db.session.flush()  # Get the provider ID
    
    # Create a contact
    contact = Contact(
        id=str(uuid.uuid4()),
        provider_id=provider.id,
        name='Test Contact',
        email='test@example.com',
        phone='123-456-7890',
        title='Manager',
        preferred_contact_method='email'
    )
    db.session.add(contact)
    
    # Create an outreach
    outreach = Outreach(
        id=str(uuid.uuid4()),
        provider_id=provider.id,
        contact_id=contact.id,
        method='email',
        notes='Test outreach',
        status='pending'
    )
    db.session.add(outreach)
    
    # Commit changes
    db.session.commit()
    
    print('Test data created successfully!')
    
    # Query and print the data
    provider = Provider.query.first()
    print(f'Provider: {provider.name}')
    print(f'Contacts: {len(provider.contacts)}')
    print(f'Outreach: {len(provider.outreach)}') 