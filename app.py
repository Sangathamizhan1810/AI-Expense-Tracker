"""
AI-Based Expense Tracker — Flask Application
=============================================
A personal expense tracking information system with AI-powered
natural language categorization, budget alerts, and spending insights.
"""

import os

from flask import Flask, render_template, g

from config import Config
from utils.db import init_app as init_db_app, init_db, get_db


def create_app():
    """Application factory: creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the instance folder exists (for SQLite DB file)
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    # Initialize database module
    init_db_app(app)

    # Auto-initialize database on first run
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            init_db()
        else:
            # Ensure tables exist even if DB file is present
            db = get_db()
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone() is None:
                init_db()

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    # ── Routes ──────────────────────────────────────────────
    from utils.auth_helpers import login_required

    @app.route('/')
    def index():
        """Landing page / home."""
        return render_template('index.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Protected dashboard placeholder (Phase 2 will implement full view)."""
        return render_template('index.html')

    # ── Context Processor ───────────────────────────────────

    @app.context_processor
    def inject_user():
        """Make current user available in all templates."""
        return dict(current_user=g.get('user', None))

    return app


# Run the app directly with `python app.py`
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
