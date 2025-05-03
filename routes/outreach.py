from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.outreach import Outreach
from models.provider import Provider
from models.contact import Contact
import uuid

outreach_bp = Blueprint("outreach", __name__, url_prefix="/outreach")

@outreach_bp.route("/")
def list_outreach():
    outreach = Outreach.query.all()
    return render_template("outreach/list.html", outreach=outreach)

@outreach_bp.route("/new", methods=["GET", "POST"])
def create_outreach():
    providers = Provider.query.all()
    contacts = Contact.query.all()
    if request.method == "POST":
        new_outreach = Outreach(
            id=str(uuid.uuid4()),
            provider_id=request.form["provider_id"],
            contact_id=request.form["contact_id"] or None,
            method=request.form["method"],
            notes=request.form["notes"],
            status=request.form["status"]
        )
        db.session.add(new_outreach)
        db.session.commit()
        flash("Outreach logged.")
        return redirect(url_for("outreach.list_outreach"))
    return render_template("outreach/form.html", providers=providers, contacts=contacts, outreach=None)

@outreach_bp.route("/<outreach_id>/edit", methods=["GET", "POST"])
def edit_outreach(outreach_id):
    outreach = Outreach.query.get_or_404(outreach_id)
    providers = Provider.query.all()
    contacts = Contact.query.all()
    if request.method == "POST":
        outreach.provider_id = request.form["provider_id"]
        outreach.contact_id = request.form["contact_id"] or None
        outreach.method = request.form["method"]
        outreach.notes = request.form["notes"]
        outreach.status = request.form["status"]
        db.session.commit()
        flash("Outreach updated.")
        return redirect(url_for("outreach.list_outreach"))
    return render_template("outreach/form.html", outreach=outreach, providers=providers, contacts=contacts)

@outreach_bp.route("/<outreach_id>/delete", methods=["POST"])
def delete_outreach(outreach_id):
    outreach = Outreach.query.get_or_404(outreach_id)
    db.session.delete(outreach)
    db.session.commit()
    flash("Outreach deleted.")
    return redirect(url_for("outreach.list_outreach"))

@outreach_bp.route("/run-jobs")
def run_jobs():
    return render_template("outreach/run_jobs.html")

@outreach_bp.route("/monitoring")
def monitoring():
    return render_template("outreach/monitoring.html") 