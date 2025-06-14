from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db
from models.provider import Provider
from models.contact import Contact
from models.outreach import Outreach
from models.intake import Intake
import uuid
import os

provider_bp = Blueprint("provider", __name__, url_prefix="/providers")

@provider_bp.route("")
def provider_root():
    """Redirect to list view."""
    return redirect(url_for("provider.list_providers"))

@provider_bp.route("/")
@login_required
def list_providers():
    providers = Provider.query.all()
    return render_template("providers/list.html", providers=providers)

@provider_bp.route("/<provider_id>/edit", methods=["GET", "POST"])
@login_required
def edit_provider(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    if request.method == "POST":
        provider.name = request.form["name"]
        provider.npi = request.form["npi"]
        provider.specialty = request.form["specialty"]
        provider.status = request.form["status"]
        db.session.commit()
        flash("Provider updated successfully!")
        return redirect(url_for("provider.list_providers"))
    return render_template("providers/new_with_contacts.html", provider=provider)

@provider_bp.route("/<provider_id>/delete", methods=["POST"])
@login_required
def delete_provider(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    db.session.delete(provider)
    db.session.commit()
    flash("Provider deleted.")
    return redirect(url_for("provider.list_providers"))

@provider_bp.route("/new-with-contacts", methods=["GET", "POST"])
@login_required
def create_provider_with_contacts():
    if request.method == "POST":
        # Create the provider
        provider = Provider(
            id=str(uuid.uuid4()),
            name=request.form["name"],
            dba_name=request.form["dba_name"],
            address=request.form["address"],
            provider_type=request.form["provider_type"],
            states_in_contract=request.form["states"],
            npi=request.form["npi"],
            specialty=request.form["specialty"],
            status=request.form["status"]
        )

        db.session.add(provider)
        db.session.commit()

        # Handle multiple contacts
        contact_names = request.form.getlist("contact_name[]")
        contact_emails = request.form.getlist("contact_email[]")
        contact_phones = request.form.getlist("contact_phone[]")
        contact_titles = request.form.getlist("contact_title[]")
        contact_preferred_methods = request.form.getlist("contact_preferred_method[]")

        for name, email, phone, title, preferred_method in zip(
            contact_names, contact_emails, contact_phones, contact_titles, contact_preferred_methods
        ):
            if name:  # skip empty rows
                contact = Contact(
                    id=str(uuid.uuid4()),
                    provider_id=provider.id,
                    name=name,
                    email=email,
                    phone=phone,
                    title=title,
                    preferred_contact_method=preferred_method
                )
                db.session.add(contact)
        db.session.commit()

        flash("Provider and contacts created successfully!")
        return redirect(url_for("provider.list_providers"))

    return render_template("providers/new_with_contacts.html")

@provider_bp.route("/api/providers/<provider_id>")
@login_required
def get_provider_api(provider_id):
    print(f"Fetching provider with ID: {provider_id}")  # Debug log
    provider = Provider.query.get(provider_id)
    if not provider:
        print(f"Provider not found for ID: {provider_id}")  # Debug log
        return jsonify({"error": "Provider not found"}), 404
    
    print(f"Found provider: {provider.name}")  # Debug log
    print(f"States in contract: {provider.states_in_contract}")  # Debug log
    
    return jsonify({
        "id": provider.id,
        "name": provider.name,
        "dba_name": provider.dba_name,
        "address": provider.address,
        "provider_type": provider.provider_type,
        "states_in_contract": provider.states_in_contract,
        "npi": provider.npi,
        "specialty": provider.specialty,
        "status": provider.status
    })

@provider_bp.route("/<provider_id>/contract-options", methods=["GET", "POST"])
@login_required
def contract_options(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    
    if request.method == "POST":
        # This is the same logic as generate_contract_route
        rate_type = request.form.get('rate_type', 'standard')
        
        custom_rates = None
        wcfs_percentages = None

        if rate_type == 'custom':
            custom_rates = {
                'mri_without': float(request.form.get('mri_without_rate', 0)),
                'mri_with': float(request.form.get('mri_with_rate', 0)),
                'mri_both': float(request.form.get('mri_both_rate', 0)),
                'ct_without': float(request.form.get('ct_without_rate', 0)),
                'ct_with': float(request.form.get('ct_with_rate', 0)),
                'ct_both': float(request.form.get('ct_both_rate', 0)),
                'xray': float(request.form.get('xray_rate', 0)),
                'arthrogram': float(request.form.get('arthrogram_rate', 0))
            }
        elif rate_type == 'wcfs':
            wcfs_percentages = {
                'mri_without': float(request.form.get('mri_without_wcfs', 80)),
                'mri_with': float(request.form.get('mri_with_wcfs', 80)),
                'mri_both': float(request.form.get('mri_both_wcfs', 80)),
                'ct_without': float(request.form.get('ct_without_wcfs', 80)),
                'ct_with': float(request.form.get('ct_with_wcfs', 80)),
                'ct_both': float(request.form.get('ct_both_wcfs', 80)),
                'xray': float(request.form.get('xray_wcfs', 80)),
                'arthrogram': float(request.form.get('arthrogram_wcfs', 80))
            }

        try:
            from utils.generate_contract import generate_contract
            docx_path, pdf_path = generate_contract(
                provider_id,
                method=rate_type,
                wcfs_percentages=wcfs_percentages,
                custom_rates=custom_rates
            )
            
            if os.path.exists(docx_path):
                flash(f"Contract generated successfully!")
                provider.contract_docx = docx_path
                
            if os.path.exists(pdf_path):
                provider.contract_pdf = pdf_path
            
            db.session.commit()
            return redirect(url_for("provider.list_providers"))
            
        except Exception as e:
            flash(f"Error generating contract: {e}")
    
    return render_template("providers/contract_options.html", provider=provider) 