from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from models import db
from models.provider import Provider
from models.contact import Contact
import uuid
import os
import json
from datetime import datetime
from utils.generate_contract import generate_contract
from utils.mailers.contract_mailer import send_contract_email, send_contract_notification

intake_bp = Blueprint("intake", __name__, url_prefix="/providers")

@intake_bp.route("/<provider_id>/generate_contract", methods=["POST"])
def generate_contract_route(provider_id):
    try:
        provider = Provider.query.get(provider_id)
        if not provider:
            flash("Provider not found")
            return redirect(url_for("provider.list_providers"))

        rate_type = request.form.get('rate_type', 'standard')
        
        # Initialize variables
        custom_rates = None
        wcfs_percentages = None

        if rate_type == 'custom':
            # Get custom dollar amounts
            custom_rates = {
                'mri_without': float(request.form['mri_without_rate']),
                'mri_with': float(request.form['mri_with_rate']),
                'mri_both': float(request.form['mri_both_rate']),
                'ct_without': float(request.form['ct_without_rate']),
                'ct_with': float(request.form['ct_with_rate']),
                'ct_both': float(request.form['ct_both_rate']),
                'xray': float(request.form['xray_rate']),
                'arthrogram': float(request.form['arthrogram_rate'])
            }
        elif rate_type == 'wcfs':
            # Get WCFS percentages
            wcfs_percentages = {
                'mri_without': float(request.form['mri_without_wcfs']),
                'mri_with': float(request.form['mri_with_wcfs']),
                'mri_both': float(request.form['mri_both_wcfs']),
                'ct_without': float(request.form['ct_without_wcfs']),
                'ct_with': float(request.form['ct_with_wcfs']),
                'ct_both': float(request.form['ct_both_wcfs']),
                'xray': float(request.form['xray_wcfs']),
                'arthrogram': float(request.form['arthrogram_wcfs'])
            }
        # For 'standard' rate type, we'll use the provider's default rates

        # Create filename using DBA name or provider name if DBA is not available
        filename = f"{provider.dba_name or provider.name}_Agreement"
        # Replace any characters that might be invalid in filenames
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
        
        docx_path, pdf_path = generate_contract(
            provider_id,
            method=rate_type,
            wcfs_percentages=wcfs_percentages,
            custom_rates=custom_rates
        )
        
        # Check if files were generated
        if os.path.exists(docx_path):
            flash(f"Contract generated successfully! DOCX file available.")
            # Update the provider with the contract file paths
            provider.contract_docx = docx_path
        else:
            flash("Error: DOCX file was not generated.")
            
        if os.path.exists(pdf_path):
            flash(f"PDF version available.")
            # Update the provider with the contract file paths
            provider.contract_pdf = pdf_path
        else:
            flash("Note: PDF conversion failed. Only DOCX version is available.")
        
        # Save the provider to update the contract file paths
        db.session.commit()
        
        # Send notification email
        try:
            send_contract_notification(provider, docx_path, pdf_path)
            flash("Notification email sent to admin.")
        except Exception as e:
            flash(f"Note: Could not send notification email: {str(e)}")
            
    except Exception as e:
        flash(f"Error generating contract: {e}")
    
    return redirect(url_for("provider.list_providers"))

@intake_bp.route("/<provider_id>/download/<file_type>")
def download_contract(provider_id, file_type):
    try:
        if file_type not in ['docx', 'pdf']:
            flash("Invalid file type")
            return redirect(url_for("provider.list_providers"))
            
        provider = Provider.query.get_or_404(provider_id)
        file_path = provider.contract_docx if file_type == 'docx' else provider.contract_pdf
        
        if not file_path or not os.path.exists(file_path):
            flash(f"Contract file not found")
            return redirect(url_for("provider.list_providers"))
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{provider.dba_name or provider.name}_Agreement.{file_type}"
        )
    except Exception as e:
        flash(f"Error downloading file: {e}")
        return redirect(url_for("provider.list_providers"))

@intake_bp.route("/<provider_id>/email_contract", methods=["POST"])
def email_contract(provider_id):
    """Email the contract to a provider contact."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        
        # Get selected contact ID from form
        contact_id = request.form.get('contact_id')
        if not contact_id:
            flash("No contact selected")
            return redirect(url_for("provider.list_providers"))
        
        # Get the contact
        contact = Contact.query.get_or_404(contact_id)
        
        # Check if contract files exist
        if not provider.contract_docx or not os.path.exists(provider.contract_docx):
            flash("Contract file not found. Please generate the contract first.")
            return redirect(url_for("provider.list_providers"))
        
        # Send email with contract
        result = send_contract_email(
            provider=provider,
            contact=contact,
            contract_docx_path=provider.contract_docx,
            contract_pdf_path=provider.contract_pdf if provider.contract_pdf else None
        )
        
        if result.get('status') == 'success':
            # Update provider status to indicate contract was sent
            provider.contract_email_sent = True
            provider.contract_email_sent_at = datetime.utcnow()
            provider.contract_email_sent_to = contact.email
            db.session.commit()
            
            flash(f"Contract emailed successfully to {contact.name} ({contact.email})")
        else:
            flash(f"Error sending email: {result.get('message')}")
        
    except Exception as e:
        flash(f"Error emailing contract: {str(e)}")
    
    return redirect(url_for("provider.list_providers"))

@intake_bp.route("/api/pending_contracts", methods=["GET"])
def api_pending_contracts():
    """API endpoint for PowerAutomate to fetch pending contracts."""
    try:
        # Find all providers with generated contracts that need processing
        providers = Provider.query.filter(
            Provider.contract_docx.isnot(None),  # Contract exists
            (Provider.contract_email_sent.is_(None) |  # Not sent by email yet
             Provider.contract_email_sent.is_(False))   
        ).all()
        
        results = []
        
        for provider in providers:
            # Skip if contract file doesn't exist
            if not os.path.exists(provider.contract_docx):
                continue
                
            # Get the primary contact if available
            contact = Contact.query.filter_by(provider_id=provider.id).first()
            
            contract_data = {
                "id": provider.id,
                "provider_name": provider.name,
                "dba_name": provider.dba_name,
                "provider_type": provider.provider_type,
                "speciality": provider.specialty,
                "npi": provider.npi,
                "states": provider.states_in_contract,
                "rate_type": provider.rate_type,
                "contract_docx_path": provider.contract_docx,
                "contract_pdf_path": provider.contract_pdf,
                "contact": {
                    "id": contact.id if contact else None,
                    "name": contact.name if contact else None,
                    "email": contact.email if contact else None,
                    "phone": contact.phone if contact else None,
                    "title": contact.title if contact else None,
                    "preferred_contact_method": contact.preferred_contact_method if contact else None
                } if contact else None,
                "docx_url": url_for('intake.download_contract', provider_id=provider.id, file_type='docx', _external=True),
                "pdf_url": url_for('intake.download_contract', provider_id=provider.id, file_type='pdf', _external=True) if provider.contract_pdf else None,
                "generated_at": provider.created_at.isoformat() if provider.created_at else None
            }
            
            results.append(contract_data)
        
        return jsonify({
            "status": "success",
            "count": len(results),
            "contracts": results
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@intake_bp.route("/api/mark_processed/<provider_id>", methods=["POST"])
def api_mark_processed(provider_id):
    """API endpoint for PowerAutomate to mark a contract as processed."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        
        # Get data from request
        data = request.json or {}
        
        # Update provider with processing information
        provider.contract_email_sent = data.get('email_sent', True)
        provider.contract_email_sent_at = datetime.utcnow()
        provider.contract_email_sent_to = data.get('sent_to')
        provider.contract_email_tracking_id = data.get('tracking_id')
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"Provider {provider_id} marked as processed",
            "provider": provider.name,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@intake_bp.route("/intake", methods=["GET", "POST"])
def intake():
    if request.method == 'POST':
        # Get provider information
        name = request.form.get('name')
        dba_name = request.form.get('dba_name')
        address = request.form.get('address')
        provider_type = request.form.get('provider_type')
        states = request.form.get('states')
        
        # Create provider
        provider = Provider(
            name=name,
            dba_name=dba_name,
            address=address,
            provider_type=provider_type,
            states_in_contract=states
        )
        db.session.add(provider)
        db.session.flush()  # Get the provider ID
        
        # Get contact information
        contact_names = request.form.getlist('contact_name[]')
        contact_phones = request.form.getlist('contact_phone[]')
        contact_emails = request.form.getlist('contact_email[]')
        
        # Create contacts
        for i in range(len(contact_names)):
            if contact_names[i]:  # Only create if name is provided
                contact = Contact(
                    provider_id=provider.id,
                    name=contact_names[i],
                    phone=contact_phones[i] if i < len(contact_phones) else None,
                    email=contact_emails[i] if i < len(contact_emails) else None
                )
                db.session.add(contact)
        
        db.session.commit()
        flash('Provider and contacts created successfully!')
        return redirect(url_for('provider.list_providers'))
    
    return render_template('providers/intake.html')