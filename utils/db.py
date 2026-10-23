"""
Database utility module.
Provides connection management, initialization, and teardown for SQLite.
"""

import os
import sqlite3

import click
from flask import current_app, g


def get_db():
    """Get a database connection for the current request.
    
    Returns a sqlite3.Connection with Row factory enabled,
    stored on Flask's `g` object for request-scoped reuse.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE']
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database by running schema.sql and seed.sql."""
    db = get_db()
    
    # Get the path to the database directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    seed_path = os.path.join(base_dir, 'database', 'seed.sql')
    
    # Execute schema
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    
    # Execute seed data
    with open(seed_path, 'r') as f:
        db.executescript(f.read())
    
    db.commit()


@click.command('init-db')
def init_db_command():
    """CLI command: Clear existing data and create fresh tables."""
    init_db()
    click.echo('✓ Database initialized successfully.')


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
