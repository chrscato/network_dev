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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__)

@email_bp.route('/send', methods=['POST'])
def send_provider_email():
    try:
        logger.debug("Starting send_provider_email")
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        
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
        logger.debug("Getting email template")
        subject, body = get_email_template(template_name, provider, contacts[0])
        logger.debug(f"Template subject: {subject}")
        
        # Parse the JSON body to get attachments
        try:
            body_json = json.loads(body)
            attachments = body_json.get('attachments', [])
            logger.debug(f"Attachments: {attachments}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON body: {str(e)}")
            attachments = []
        
        # Send email to configured address
        recipient = current_app.config['CDX_EMAIL']
        logger.debug(f"Recipient email: {recipient}")
        if not recipient:
            return jsonify({'error': 'Recipient email not configured in environment variables'}), 500
        
        # Send email with attachments
        logger.debug("Attempting to send email")
        send_email(
            to_email=recipient,
            subject=subject,
            body=body,
            attachments=attachments
        )
        logger.debug("Email sent successfully")
        
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
        logger.error(f"Error in send_provider_email: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500 