from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required
from models import db
from models.outreach import Outreach
from models.provider import Provider
from models.contact import Contact
from models.intake import Intake
from datetime import datetime
import json
from utils.check_replies import check_all_recent_outreach

outreach_bp = Blueprint('outreach', __name__)

@outreach_bp.route("/outreach")
@login_required
def list_outreach():
    """List all outreach activities."""
    outreach_entries = Outreach.query.order_by(Outreach.created_at.desc()).all()
    return render_template("outreach/list.html", outreach=outreach_entries)

@outreach_bp.route("/outreach/new", methods=["GET", "POST"])
@login_required
def new_outreach():
    """Create a new outreach activity."""
    if request.method == "POST":
        outreach = Outreach(
            provider_id=request.form["provider_id"],
            contact_id=request.form.get("contact_id"),
            type=request.form["type"],
            method=request.form.get("method", "email"),  # Default to email
            status=request.form["status"],
            notes=request.form.get("notes")
        )
        db.session.add(outreach)
        db.session.commit()
        flash("Outreach activity created successfully!", "success")
        return redirect(url_for("outreach.list_outreach"))
    
    providers = Provider.query.all()
    contacts = Contact.query.all()
    return render_template("outreach/new.html", providers=providers, contacts=contacts)

@outreach_bp.route("/outreach/<outreach_id>")
@login_required
def view_outreach(outreach_id):
    """View a single outreach activity."""
    outreach = Outreach.query.get_or_404(outreach_id)
    return render_template("outreach/view.html", outreach=outreach)

@outreach_bp.route("/outreach/<outreach_id>/edit", methods=["GET", "POST"])
@login_required
def edit_outreach(outreach_id):
    """Edit an outreach activity."""
    outreach = Outreach.query.get_or_404(outreach_id)
    if request.method == "POST":
        outreach.provider_id = request.form["provider_id"]
        outreach.contact_id = request.form.get("contact_id")
        outreach.type = request.form["type"]
        outreach.method = request.form.get("method", "email")
        outreach.status = request.form["status"]
        outreach.notes = request.form.get("notes")
        db.session.commit()
        flash("Outreach activity updated successfully!", "success")
        return redirect(url_for("outreach.view_outreach", outreach_id=outreach.id))
    
    providers = Provider.query.all()
    contacts = Contact.query.all()
    return render_template("outreach/edit.html", outreach=outreach, providers=providers, contacts=contacts)

@outreach_bp.route("/outreach/<outreach_id>/delete", methods=["POST"])
@login_required
def delete_outreach(outreach_id):
    """Delete an outreach activity."""
    outreach = Outreach.query.get_or_404(outreach_id)
    db.session.delete(outreach)
    db.session.commit()
    flash("Outreach activity deleted successfully!", "success")
    return redirect(url_for("outreach.list_outreach"))

@outreach_bp.route("/api/outreach")
@login_required
def api_outreach():
    """API endpoint to get all outreach activities."""
    outreach_entries = Outreach.query.all()
    return jsonify([{
        'id': o.id,
        'provider_id': o.provider_id,
        'contact_id': o.contact_id,
        'type': o.type,
        'method': o.method,
        'status': o.status,
        'notes': o.notes,
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'updated_at': o.updated_at.isoformat() if o.updated_at else None,
        'reply_received': o.reply_received,
        'reply_status': o.reply_status,
        'reply_count': o.reply_count,
        'last_reply_date': o.last_reply_date.isoformat() if o.last_reply_date else None
    } for o in outreach_entries])

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

@outreach_bp.route("/check-replies", methods=["GET", "POST"])
@login_required
def check_replies_now():
    """Manually trigger reply checking via web interface."""
    try:
        with current_app.app_context():
            replies_found = check_all_recent_outreach(days_back=7)
        
        if replies_found > 0:
            flash(f"✅ Reply check completed! Found {replies_found} new replies.", "success")
        else:
            flash("📭 Reply check completed. No new replies found.", "info")
        
    except Exception as e:
        flash(f"❌ Error checking replies: {str(e)}", "error")
    
    return redirect(url_for("outreach.list_outreach"))

@outreach_bp.route("/<outreach_id>/mark-read", methods=["POST"])
@login_required
def mark_reply_read(outreach_id):
    """Mark a reply as read."""
    try:
        outreach = Outreach.query.get_or_404(outreach_id)
        outreach.mark_reply_read()
        return jsonify({"success": True, "message": "Reply marked as read"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@outreach_bp.route("/<outreach_id>/mark-responded", methods=["POST"])
@login_required
def mark_reply_responded(outreach_id):
    """Mark a reply as responded to."""
    try:
        outreach = Outreach.query.get_or_404(outreach_id)
        outreach.mark_reply_responded()
        return jsonify({"success": True, "message": "Reply marked as responded"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500 