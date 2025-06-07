from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Simple test model
class TestModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

@app.route('/')
def home():
    return 'Home page is working!'

@app.route('/db-test')
def db_test():
    # Simple DB query test
    try:
        count = TestModel.query.count()
        return f'Database connection successful. Found {count} items.'
    except Exception as e:
        return f'Database error: {str(e)}'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True, port=5050)