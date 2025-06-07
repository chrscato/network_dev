from flask import Blueprint, request, jsonify, flash, redirect, url_for, current_app
from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach
from utils.email_templates import get_email_template
from datetime import datetime
import os
import logging
import json
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__, url_prefix='/email')

@email_bp.route('/send', methods=['POST'])
def send_provider_email():
    try:
        logger.debug("Starting send_provider_email")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        logger.debug(f"Received data: {data}")
        
        provider_id = data.get('provider_id')
        template_name = data.get('template_name', 'provider_outreach_cold')
        
        if not provider_id:
            error_msg = 'Provider ID is required'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
        # Get provider and contacts
        provider = Provider.query.get(provider_id)
        if not provider:
            error_msg = 'Provider not found'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'error': error_msg}), 404
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
        contacts = Contact.query.filter_by(provider_id=provider_id).all()
        if not contacts:
            error_msg = 'No contacts found for provider'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'error': error_msg}), 404
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
        # Get email template
        logger.debug("Getting email template")
        subject, body = get_email_template(template_name, provider, contacts[0])
        logger.debug(f"Template subject: {subject}")
        
        # Parse the JSON body to get outreach template content
        try:
            body_json = json.loads(body)
            outreach_template = body_json.get('outreach_template', {})
            email_subject = outreach_template.get('subject', subject)
            email_body = outreach_template.get('body', 'Default email body')
            attachments = body_json.get('attachments', [])
            logger.debug(f"Outreach template: {outreach_template}")
            logger.debug(f"Attachments: {attachments}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON body: {str(e)}")
            email_subject = subject
            email_body = "Error parsing email template"
            attachments = []
        
        # Send email to configured address or the contact's email
        recipient = contacts[0].email
        logger.debug(f"Recipient email: {recipient}")
        
        if not recipient:
            error_msg = 'No recipient email configured'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
        # Import the email service
        try:
            from utils.mailers.mail_service import send_email_with_file_attachments
            logger.debug("Imported mail service successfully")
        except ImportError as e:
            logger.error(f"Failed to import mail service: {e}")
            error_msg = f'Email service not available: {str(e)}'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
        # Prepare file paths for attachments
        file_paths = []
        if attachments:
            for attachment in attachments:
                file_path = attachment.get('path')
                if file_path and os.path.exists(file_path):
                    file_paths.append(file_path)
                    logger.debug(f"Added attachment: {file_path}")
                else:
                    logger.warning(f"Attachment file not found: {file_path}")
        
        # Send email with attachments
        logger.debug("Attempting to send email")
        result = send_email_with_file_attachments(
            subject=email_subject,
            body=email_body,
            recipient=recipient,
            file_paths=file_paths
        )
        logger.debug(f"Email send result: {result}")
        
        if result.get('status') == 'success':
            logger.info("Email sent successfully")
            
            # Update provider status
            provider.status = 'outreach'
            
            # Create outreach record with tracking info
            outreach = Outreach(
                id=str(uuid.uuid4()),
                provider_id=provider_id,
                contact_id=contacts[0].id,
                method='email',
                type='cold',
                notes=f'Sent {template_name} email to {recipient}',
                status='sent'
            )
            
            # Add tracking information if available
            if result.get('message_id') and result.get('conversation_id'):
                outreach.update_email_tracking(
                    message_id=result['message_id'],
                    conversation_id=result['conversation_id']
                )
                logger.info(f"Stored tracking info - Message ID: {result['message_id']}, Conversation ID: {result['conversation_id']}")
            
            db.session.add(outreach)
            db.session.commit()
            
            success_msg = f'Email sent successfully to {recipient}'
            if request.is_json:
                return jsonify({
                    'message': success_msg,
                    'provider_id': provider_id,
                    'outreach_id': outreach.id,
                    'message_id': result.get('message_id'),
                    'conversation_id': result.get('conversation_id')
                })
            else:
                flash(success_msg)
                return redirect(url_for("provider.list_providers"))
        else:
            error_msg = f'Failed to send email: {result.get("message", "Unknown error")}'
            logger.error(error_msg)
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg)
                return redirect(url_for("provider.list_providers"))
        
    except Exception as e:
        logger.error(f"Error in send_provider_email: {str(e)}", exc_info=True)
        error_msg = f'Unexpected error: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg)
            return redirect(url_for("provider.list_providers")) 