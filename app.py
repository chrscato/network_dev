from flask import Flask, render_template
from flask_migrate import Migrate
from config import Config
from models import db
from models import provider, contact, outreach
from routes.providers import provider_bp
from routes.contacts import contact_bp
from routes.outreach import outreach_bp
from routes.intake import intake_bp
# In app.py, add this import
from routes.test_api import test_api_bp
from routes.email import email_bp
import argparse



app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(provider_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(outreach_bp)
app.register_blueprint(intake_bp)
app.register_blueprint(test_api_bp)
app.register_blueprint(email_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=True)