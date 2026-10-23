"""
Auth helpers: user queries, creation, login_required decorator, and user loading.
"""

import functools
import re
from flask import session, redirect, url_for, flash, g, request
from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import get_db

EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')


def get_user_by_id(user_id):
    """Fetch a user row by ID."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return user


def get_user_by_email(email):
    """Fetch a user row by email address."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email.strip().lower(),)).fetchone()
    return user


def create_user(name, email, password):
    """
    Validate inputs and create a new user in the database.
    Returns the newly created user dict or raises ValueError with a descriptive message.
    """
    name = (name or '').strip()
    email = (email or '').strip().lower()

    if not name or len(name) < 2 or len(name) > 50:
        raise ValueError("Name must be between 2 and 50 characters.")

    if not email or not EMAIL_REGEX.match(email):
        raise ValueError("Please provide a valid email address.")

    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    db = get_db()
    existing_user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing_user is not None:
        raise ValueError(f"An account with email {email} already exists.")

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    cursor = db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    db.commit()

    return get_user_by_id(cursor.lastrowid)


def login_required(view):
    """Decorator: redirect to login if user is not authenticated."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login', next=request.path if 'request' in globals() else None))
        return view(**kwargs)
    return wrapped_view


def load_logged_in_user():
    """Load current user into g.user based on session['user_id']."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_user_by_id(user_id)
