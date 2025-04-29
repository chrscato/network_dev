from flask import Flask, render_template
from flask_migrate import Migrate
from config import Config
from models import db
from models import provider, contact, outreach
from routes.providers import provider_bp
from routes.contacts import contact_bp
from routes.outreach import outreach_bp
from routes.intake import intake_bp

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(provider_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(outreach_bp)
app.register_blueprint(intake_bp)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True) 