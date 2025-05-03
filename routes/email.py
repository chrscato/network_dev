from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app
from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach
from utils.mailers.emailer import send_email
from utils.email_templates import get_email_template
from datetime import datetime
import os
import logging
import json
import uuid

email_bp = Blueprint('email', __name__)

@email_bp.route('/send', methods=['POST'])
def send_provider_email():
    try:
        data = request.get_json()
        provider_id = data.get('provider_id')
        template_name = data.get('template_name', 'provider_outreach_cold')
        
        if not provider_id:
            return jsonify({'error': 'Provider ID is required'}), 400
        
        # Get provider and contacts
        provider = Provider.query.get(provider_id)
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404
        
        contacts = Contact.query.filter_by(provider_id=provider_id).all()
        if not contacts:
            return jsonify({'error': 'No contacts found for provider'}), 404
        
        # Get email template
        subject, body = get_email_template(template_name, provider, contacts[0])
        
        # Parse the JSON body to get attachments
        try:
            body_json = json.loads(body)
            attachments = body_json.get('attachments', [])
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON body: {str(e)}")
            attachments = []
        
        # Send email to configured address
        recipient = os.getenv('CDX_EMAIL')
        if not recipient:
            return jsonify({'error': 'Recipient email not configured in environment variables'}), 500
        
        # Send email with attachments
        send_email(
            to_email=recipient,
            subject=subject,
            body=body,
            attachments=attachments
        )
        
        # Update provider status
        provider.status = 'outreach'
        
        # Create outreach record
        outreach = Outreach(
            id=str(uuid.uuid4()),
            provider_id=provider_id,
            contact_id=contacts[0].id,
            method='email',
            type='cold',  # Since we're using the cold outreach template
            notes=f'Sent {template_name} email',
            status='completed'
        )
        db.session.add(outreach)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': 'Email sent successfully',
            'provider_id': provider_id,
            'status': provider.status,
            'outreach_id': outreach.id
        })
        
    except Exception as e:
        logging.error(f"Error in send_provider_email: {str(e)}")
        return jsonify({'error': str(e)}), 500 