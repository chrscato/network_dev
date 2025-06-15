from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required
from models import db
from models.provider import Provider
from models.contact import Contact
from models.intake import Intake
import uuid
import os
import json
from datetime import datetime
from utils.generate_contract import generate_contract, generate_contract_per_state, IMAGING_CATEGORIES
from utils.mailers.contract_mailer import send_contract_email, send_contract_notification

intake_bp = Blueprint("intake", __name__, url_prefix="/intakes")

@intake_bp.route("/")
@login_required
def list_intakes():
    """List all intakes."""
    intakes = Intake.query.all()
    return render_template("intakes/list.html", intakes=intakes)

@intake_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_intake():
    """Create a new intake."""
    if request.method == "POST":
        intake = Intake(
            provider_id=request.form["provider_id"],
            contact_id=request.form.get("contact_id"),
            type=request.form["type"],
            status=request.form["status"],
            notes=request.form.get("notes")
        )
        db.session.add(intake)
        db.session.commit()
        flash("Intake created successfully!", "success")
        return redirect(url_for("intake.list_intakes"))
    
    providers = Provider.query.all()
    contacts = Contact.query.all()
    return render_template("intakes/new.html", providers=providers, contacts=contacts)

@intake_bp.route("/<intake_id>")
@login_required
def view_intake(intake_id):
    """View a single intake."""
    intake = Intake.query.get_or_404(intake_id)
    return render_template("intakes/view.html", intake=intake)

@intake_bp.route("/<intake_id>/edit", methods=["GET", "POST"])
@login_required
def edit_intake(intake_id):
    """Edit an existing intake."""
    intake = Intake.query.get_or_404(intake_id)
    if request.method == "POST":
        intake.provider_id = request.form["provider_id"]
        intake.contact_id = request.form.get("contact_id")
        intake.type = request.form["type"]
        intake.status = request.form["status"]
        intake.notes = request.form.get("notes")
        db.session.commit()
        flash("Intake updated successfully!", "success")
        return redirect(url_for("intake.view_intake", intake_id=intake.id))
    
    providers = Provider.query.all()
    contacts = Contact.query.all()
    return render_template("intakes/edit.html", intake=intake, providers=providers, contacts=contacts)

@intake_bp.route("/<intake_id>/delete", methods=["POST"])
@login_required
def delete_intake(intake_id):
    """Delete an intake."""
    intake = Intake.query.get_or_404(intake_id)
    db.session.delete(intake)
    db.session.commit()
    flash("Intake deleted successfully!", "success")
    return redirect(url_for("intake.list_intakes"))

@intake_bp.route("/api/intakes")
@login_required
def api_intakes():
    """API endpoint to get all intakes."""
    intakes = Intake.query.all()
    return jsonify([intake.to_dict() for intake in intakes])

@intake_bp.route("/<provider_id>/configure_contract", methods=["GET"])
@login_required
def configure_contract(provider_id):
    """Configure contract rates for a provider."""
    provider = Provider.query.get_or_404(provider_id)
    
    # Parse states from provider
    if provider.states_in_contract:
        states = [s.strip() for s in provider.states_in_contract.split(",") if s.strip()]
    else:
        states = ["CA"]  # Default to California
    
    return render_template(
        "providers/configure_contract.html", 
        provider=provider, 
        states=states,
        imaging_categories=IMAGING_CATEGORIES
    )

@intake_bp.route("/<provider_id>/generate_contract", methods=["POST"])
@login_required
def generate_contract_route(provider_id):
    """Generate a contract for a provider."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        
        # Parse states
        if provider.states_in_contract:
            states = [s.strip() for s in provider.states_in_contract.split(",") if s.strip()]
        else:
            states = ["CA"]
        
        # Process per-state rate configurations
        state_configurations = {}
        
        for state in states:
            rate_type = request.form.get(f'rate_type_{state}', 'standard')
            state_config = {'method': rate_type}
            
            if rate_type == 'wcfs':
                # Collect WCFS percentages for this state
                wcfs_data = {}
                for category in IMAGING_CATEGORIES:
                    field_name = f"wcfs_{state}_{category.replace(' ', '_').replace('&', 'and').lower()}"
                    percentage = request.form.get(field_name)
                    if percentage:
                        wcfs_data[category] = float(percentage)
                state_config['wcfs_percentages'] = wcfs_data
                
            elif rate_type == 'custom':
                # Collect custom rates for this state
                custom_data = {}
                for category in IMAGING_CATEGORIES:
                    field_name = f"custom_{state}_{category.replace(' ', '_').replace('&', 'and').lower()}"
                    rate = request.form.get(field_name)
                    if rate:
                        custom_data[category] = float(rate)
                state_config['custom_rates'] = custom_data
            
            state_configurations[state] = state_config
        
        # Generate contract with per-state configuration
        docx_path, pdf_path = generate_contract_per_state(provider_id, state_configurations)
        
        # Update provider with contract file paths
        if docx_path and os.path.exists(docx_path):
            provider.contract_docx = docx_path
            flash("Contract generated successfully! DOCX file available.")
            
            # Try to convert to PDF
            if pdf_path and os.path.exists(pdf_path):
                provider.contract_pdf = pdf_path
                flash("PDF version available.")
            else:
                flash("Note: PDF conversion failed. You can try converting again later.")
        
        db.session.commit()
        
    except Exception as e:
        flash(f"Error generating contract: {e}")
    
    return redirect(url_for("provider.list_providers"))

@intake_bp.route("/<provider_id>/download/<file_type>")
@login_required
def download_contract(provider_id, file_type):
    """Download a contract file."""
    try:
        if file_type not in ['docx', 'pdf']:
            flash("Invalid file type", "error")
            return redirect(url_for("provider.list_providers"))
            
        provider = Provider.query.get_or_404(provider_id)
        file_path = provider.contract_docx if file_type == 'docx' else provider.contract_pdf
        
        if not file_path or not os.path.exists(file_path):
            flash("Contract file not found", "error")
            return redirect(url_for("provider.list_providers"))
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{provider.dba_name or provider.name}_Agreement.{file_type}"
        )
    except Exception as e:
        flash(f"Error downloading file: {e}", "error")
        return redirect(url_for("provider.list_providers"))

@intake_bp.route("/<provider_id>/email_contract", methods=["POST"])
@login_required
def email_contract(provider_id):
    """Email a contract to a provider contact."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        
        contact_id = request.form.get('contact_id')
        if not contact_id:
            flash("No contact selected", "error")
            return redirect(url_for("provider.list_providers"))
        
        contact = Contact.query.get_or_404(contact_id)
        
        if not provider.contract_docx or not os.path.exists(provider.contract_docx):
            flash("Contract file not found. Please generate the contract first.", "error")
            return redirect(url_for("provider.list_providers"))
        
        result = send_contract_email(
            provider=provider,
            contact=contact,
            contract_docx_path=provider.contract_docx,
            contract_pdf_path=provider.contract_pdf if provider.contract_pdf else None
        )
        
        if result.get('status') == 'success':
            provider.contract_email_sent = True
            provider.contract_email_sent_at = datetime.utcnow()
            provider.contract_email_sent_to = contact.email
            db.session.commit()
            
            flash(f"Contract emailed successfully to {contact.name} ({contact.email})", "success")
        else:
            flash(f"Error sending email: {result.get('message')}", "error")
        
    except Exception as e:
        flash(f"Error emailing contract: {str(e)}", "error")
    
    return redirect(url_for("provider.list_providers"))

@intake_bp.route("/<provider_id>/convert_to_pdf", methods=["POST"])
@login_required
def convert_to_pdf(provider_id):
    """Convert existing DOCX contract to PDF."""
    try:
        provider = Provider.query.get_or_404(provider_id)
        
        if not provider.contract_docx or not os.path.exists(provider.contract_docx):
            flash("DOCX contract not found", "error")
            return redirect(url_for("provider.list_providers"))
            
        # Convert DOCX to PDF using docx2pdf
        from utils.generate_contract import convert_docx_to_pdf
        pdf_path = convert_docx_to_pdf(provider.contract_docx)
        
        if pdf_path and os.path.exists(pdf_path):
            provider.contract_pdf = pdf_path
            db.session.commit()
            flash("PDF version generated successfully!", "success")
        else:
            flash("PDF conversion failed. Please ensure docx2pdf is installed.", "error")
            
        return redirect(url_for("provider.list_providers"))
        
    except Exception as e:
        flash(f"Error converting to PDF: {e}", "error")
        return redirect(url_for("provider.list_providers"))