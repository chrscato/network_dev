from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, current_user, login_required
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.authenticate(username, password)
        if user:
            login_user(user, remember=True)  # Remember for 30 days by default
            flash('Login successful!', 'success')
            # Get the next page from the query string, default to home
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('home')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    # For GET requests, show the login form
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login')) 