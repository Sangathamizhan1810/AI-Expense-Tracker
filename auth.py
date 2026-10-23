"""
AI-Based Expense Tracker — Authentication Blueprint
===================================================
Handles user registration, login, logout, and session lifecycle.
"""

from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash

from utils.auth_helpers import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    load_logged_in_user
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.before_app_request
def before_request():
    """Load logged-in user into g.user before every request."""
    load_logged_in_user()


def _is_safe_url(target):
    """Check if redirect target is a safe local URL."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('', 'http', 'https') and (
        not test_url.netloc or test_url.netloc == ref_url.netloc
    ) and target.startswith('/') and not target.startswith('//')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # If already logged in, redirect home
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Passwords matching check
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', name=name, email=email)

        try:
            create_user(name, email, password)
            flash('Registration successful! Please sign in.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('auth/register.html', name=name, email=email)
        except Exception as e:
            flash('An unexpected error occurred during registration. Please try again.', 'error')
            return render_template('auth/register.html', name=name, email=email)

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and session initialization."""
    # If already logged in, redirect home
    if g.user:
        return redirect(url_for('index'))

    next_url = request.args.get('next')

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        submitted_next = request.form.get('next')

        user = get_user_by_email(email)

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email, next=submitted_next or next_url)

        # Login successful — initialize session
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session.permanent = True

        flash(f"Welcome back, {user['name']}!", 'success')

        redirect_target = submitted_next or next_url
        if redirect_target and _is_safe_url(redirect_target):
            return redirect(redirect_target)
        return redirect(url_for('index'))

    return render_template('auth/login.html', next=next_url)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log out current user and clear session."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))
