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

@outreach_bp.route("/analytics")
def analytics():
    """Show outreach analytics and reply tracking."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get date range (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Basic metrics
    total_outreach = Outreach.query.filter(
        Outreach.created_at >= start_date,
        Outreach.method == 'email'
    ).count()
    
    outreach_with_tracking = Outreach.query.filter(
        Outreach.created_at >= start_date,
        Outreach.method == 'email',
        Outreach.conversation_id.isnot(None)
    ).count()
    
    # Get all tracked outreach for reply analysis
    tracked_outreach = Outreach.query.filter(
        Outreach.created_at >= start_date,
        Outreach.method == 'email',
        Outreach.conversation_id.isnot(None)
    ).all()
    
    # Count replies (basic check - you can enhance this)
    replies_found = sum(1 for o in tracked_outreach if 'Reply received:' in (o.notes or ''))
    
    # Calculate response rate
    response_rate = (replies_found / outreach_with_tracking * 100) if outreach_with_tracking > 0 else 0
    
    # Recent outreach with tracking info
    recent_outreach = Outreach.query.filter(
        Outreach.created_at >= start_date,
        Outreach.method == 'email'
    ).order_by(Outreach.created_at.desc()).limit(20).all()
    
    analytics_data = {
        'total_outreach': total_outreach,
        'outreach_with_tracking': outreach_with_tracking,
        'replies_found': replies_found,
        'response_rate': round(response_rate, 1),
        'recent_outreach': recent_outreach,
        'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    }
    
    return render_template("outreach/analytics.html", analytics=analytics_data)

@outreach_bp.route("/check-replies", methods=["POST"])
def check_replies_now():
    """Manually trigger reply checking via web interface."""
    import json
    from utils.check_replies import check_all_recent_outreach
    
    try:
        # Capture the output by redirecting it
        import io
        import contextlib
        
        # Create a string buffer to capture print statements
        output_buffer = io.StringIO()
        
        with contextlib.redirect_stdout(output_buffer):
            # Run the reply checker
            from app import app
            with app.app_context():
                check_all_recent_outreach(days_back=7)
        
        # Get the captured output
        output = output_buffer.getvalue()
        
        # Parse results (basic parsing of the output)
        lines = output.split('\n')
        checking_line = [line for line in lines if 'Checking' in line and 'outreach records' in line]
        total_line = [line for line in lines if 'Total replies found:' in line]
        
        if checking_line:
            records_checked = checking_line[0].split()[1] if len(checking_line[0].split()) > 1 else '0'
        else:
            records_checked = '0'
            
        if total_line:
            replies_found = total_line[0].split()[-1] if total_line else '0'
        else:
            replies_found = '0'
        
        flash(f"Reply check completed! Checked {records_checked} records, found {replies_found} replies.")
        
    except Exception as e:
        flash(f"Error checking replies: {str(e)}")
    
    return redirect(url_for("outreach.analytics")) 