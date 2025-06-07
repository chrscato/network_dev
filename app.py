from flask import Flask, render_template, jsonify, request
from flask_migrate import Migrate
from config import Config
from models import db
from models import provider, contact, outreach
from routes.providers import provider_bp
from routes.contacts import contact_bp
from routes.outreach import outreach_bp
from routes.intake import intake_bp
from routes.test_api import test_api_bp
from routes.test_graph_email import test_graph_email_bp
from routes.email import email_bp
import os
import logging

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this debug code temporarily
print("=== DEBUGGING BLUEPRINT REGISTRATION ===")
try:
    from routes.email import email_bp as debug_email_bp
    print(f"✅ Email blueprint imported: {debug_email_bp.name} with prefix {debug_email_bp.url_prefix}")
except Exception as e:
    print(f"❌ Email blueprint import failed: {e}")

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
db.init_app(app)
migrate = Migrate(app, db)

# Check if Microsoft Graph API is configured
graph_vars = ["MS_GRAPH_CLIENT_ID", "MS_GRAPH_CLIENT_SECRET", "MS_GRAPH_TENANT_ID", "MS_GRAPH_USER_EMAIL"]
missing_vars = [var for var in graph_vars if not os.getenv(var)]

if missing_vars:
    logger.warning(f"Microsoft Graph API is not fully configured. Missing: {', '.join(missing_vars)}")
    logger.warning("Falling back to Gmail SMTP")
else:
    logger.info("Microsoft Graph API is properly configured")

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return render_template('error.html', error=error), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error: {error}")
    return render_template('error.html', error=error), 404

@app.route("/debug-routes")
def debug_routes():
    """List all registered routes for debugging."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule),
            "defaults": rule.defaults,
            "arguments": list(rule.arguments)
        })
    
    return jsonify({
        "total_routes": len(routes),
        "routes": routes
    })

# Add some simple test routes directly to app.py
@app.route("/hello")
def hello():
    return "Hello, World!"

@app.route("/test-providers")
def test_providers():
    return "Provider test route"

# Register blueprints
app.register_blueprint(provider_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(outreach_bp)
app.register_blueprint(intake_bp)
app.register_blueprint(test_api_bp)
app.register_blueprint(test_graph_email_bp)

print("Registering email blueprint...")
app.register_blueprint(email_bp)
print("✅ Email blueprint registered successfully")

# Debug: Check if email routes are registered
print("=== CHECKING REGISTERED ROUTES ===")
email_routes = [str(rule) for rule in app.url_map.iter_rules() if rule.endpoint and rule.endpoint.startswith('email.')]
print(f"Found {len(email_routes)} email routes: {email_routes}")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)