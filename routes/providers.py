from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.provider import Provider
from models.contact import Contact
import uuid

provider_bp = Blueprint("provider", __name__, url_prefix="/providers")

@provider_bp.route("/")
def list_providers():
    providers = Provider.query.all()
    return render_template("providers/list.html", providers=providers)

@provider_bp.route("/<provider_id>/edit", methods=["GET", "POST"])
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
def delete_provider(provider_id):
    provider = Provider.query.get_or_404(provider_id)
    db.session.delete(provider)
    db.session.commit()
    flash("Provider deleted.")
    return redirect(url_for("provider.list_providers"))

@provider_bp.route("/new-with-contacts", methods=["GET", "POST"])
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