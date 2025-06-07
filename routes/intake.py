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
from utils.generate_contract import generate_contract
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

# Contract-related routes
@intake_bp.route("/<provider_id>/generate_contract", methods=["POST"])
@login_required
def generate_contract_route(provider_id):
    """Generate a contract for a provider."""
    try:
        provider = Provider.query.get(provider_id)
        if not provider:
            flash("Provider not found", "error")
            return redirect(url_for("provider.list_providers"))

        rate_type = request.form.get('rate_type', 'standard')
        
        # Initialize variables
        custom_rates = None
        wcfs_percentages = None

        if rate_type == 'custom':
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

        filename = f"{provider.dba_name or provider.name}_Agreement"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
        
        docx_path, pdf_path = generate_contract(
            provider_id,
            method=rate_type,
            wcfs_percentages=wcfs_percentages,
            custom_rates=custom_rates
        )
        
        if os.path.exists(docx_path):
            flash("Contract generated successfully!", "success")
            provider.contract_docx = docx_path
        else:
            flash("Error: DOCX file was not generated.", "error")
            
        if os.path.exists(pdf_path):
            flash("PDF version available.", "success")
            provider.contract_pdf = pdf_path
        else:
            flash("Note: PDF conversion failed. Only DOCX version is available.", "warning")
        
        db.session.commit()
        
        try:
            send_contract_notification(provider, docx_path, pdf_path)
            flash("Notification email sent to admin.", "success")
        except Exception as e:
            flash(f"Note: Could not send notification email: {str(e)}", "warning")
            
    except Exception as e:
        flash(f"Error generating contract: {e}", "error")
    
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