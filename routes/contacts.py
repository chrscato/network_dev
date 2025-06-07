from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db
from models.contact import Contact
from models.provider import Provider
from models.outreach import Outreach
from models.intake import Intake
from datetime import datetime
import json

contact_bp = Blueprint("contact", __name__, url_prefix="/contacts")

@contact_bp.route("/")
@login_required
def list_contacts():
    contacts = Contact.query.all()
    return render_template("contacts/list.html", contacts=contacts)

@contact_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_contact():
    providers = Provider.query.all()
    if request.method == "POST":
        new_contact = Contact(
            id=str(uuid.uuid4()),
            provider_id=request.form["provider_id"],
            name=request.form["name"],
            email=request.form["email"],
            phone=request.form["phone"],
            title=request.form["title"],
            preferred_contact_method=request.form["preferred_contact_method"]
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("Contact added.")
        return redirect(url_for("contact.list_contacts"))
    return render_template("contacts/form.html", providers=providers, contact=None)

@contact_bp.route("/<contact_id>/edit", methods=["GET", "POST"])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    providers = Provider.query.all()
    if request.method == "POST":
        contact.provider_id = request.form["provider_id"]
        contact.name = request.form["name"]
        contact.email = request.form["email"]
        contact.phone = request.form["phone"]
        contact.title = request.form["title"]
        contact.preferred_contact_method = request.form["preferred_contact_method"]
        db.session.commit()
        flash("Contact updated.")
        return redirect(url_for("contact.list_contacts"))
    return render_template("contacts/form.html", contact=contact, providers=providers)

@contact_bp.route("/<contact_id>/delete", methods=["POST"])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Contact deleted.")
    return redirect(url_for("contact.list_contacts"))

@contact_bp.route("/api/contacts")
@login_required
def api_contacts():
    contacts = Contact.query.all()
    return jsonify([{
        'id': c.id,
        'provider_id': c.provider_id,
        'name': c.name,
        'title': c.title,
        'email': c.email,
        'phone': c.phone,
        'status': c.status
    } for c in contacts]) 