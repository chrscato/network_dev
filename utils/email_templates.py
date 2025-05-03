import yaml
import os
import json
from flask import current_app
from datetime import datetime

def load_email_templates():
    """Load email templates from YAML file."""
    template_path = os.path.join(current_app.root_path, 'config', 'email_templates.yaml')
    with open(template_path, 'r') as file:
        return yaml.safe_load(file)

def get_email_template(template_name, provider, contact=None):
    """
    Get a formatted email template with provider and contact information.
    
    Args:
        template_name (str): Name of the template to use
        provider (Provider): Provider model instance
        contact (Contact, optional): Contact model instance
        
    Returns:
        tuple: (subject, body) where body is a JSON string
    """
    templates = load_email_templates()
    template = templates['templates'][template_name]
    
    # Prepare template variables
    template_vars = {
        # Metadata
        'timestamp': datetime.utcnow().isoformat(),
        'provider_id': provider.id,
        
        # Provider Basic Info
        'provider_name': provider.name,
        'dba_name': provider.dba_name if provider.dba_name else "",
        'specialty': provider.specialty if provider.specialty else "",
        'npi': provider.npi if provider.npi else "",
        'provider_type': provider.provider_type if provider.provider_type else "",
        
        # Provider Location
        'address': provider.address if provider.address else "",
        'states': provider.states_in_contract if provider.states_in_contract else "",
        
        # Provider Status
        'status': provider.status if provider.status else "pending",
        
        # Contact Info
        'recipient_name': contact.name if contact else 'Provider',
        'contact_title': contact.title if contact and contact.title else "",
        'contact_email': contact.email if contact and contact.email else "",
        'contact_phone': contact.phone if contact and contact.phone else "",
        'preferred_contact': contact.preferred_contact_method if contact and contact.preferred_contact_method else "",
        
        # Template-specific
        'specialty_info': f" ({provider.specialty})" if provider.specialty else ""
    }
    
    # Format the template body as JSON
    body = template['body']
    
    # Convert to string with proper formatting
    formatted_body = json.dumps(body, indent=2)
    
    # Replace all template variables
    for key, value in template_vars.items():
        formatted_body = formatted_body.replace(f"{{{key}}}", str(value))
    
    return template['subject'].format(**template_vars), formatted_body 