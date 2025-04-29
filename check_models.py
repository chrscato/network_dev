from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach

# Print table information
print('Provider table:', Provider.__table__.columns.keys())
print('Contact table:', Contact.__table__.columns.keys())
print('Outreach table:', Outreach.__table__.columns.keys())

# Check relationships
print('\nProvider relationships:')
for rel in Provider.__mapper__.relationships:
    print(f'  {rel.key}: {rel.target}')

print('\nContact relationships:')
for rel in Contact.__mapper__.relationships:
    print(f'  {rel.key}: {rel.target}')

print('\nOutreach relationships:')
for rel in Outreach.__mapper__.relationships:
    print(f'  {rel.key}: {rel.target}') 