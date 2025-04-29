from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import db
from models.provider import Provider
from models.contact import Contact
import uuid
import os
from utils.generate_contract import generate_contract

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
            states=states
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