"""
Phase 1 Verification Tests
Tests database initialization, schema integrity, category seeding, and authentication lifecycle.
"""

import unittest
import os
import tempfile
from app import create_app
from utils.db import get_db, init_db
from utils.auth_helpers import create_user, get_user_by_email, get_user_by_id


class Phase1TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_database_tables_and_seed(self):
        """Verify all 4 tables exist and 8 default categories are seeded."""
        with self.app.app_context():
            db = get_db()
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row['name'] for row in cursor.fetchall()]
            self.assertIn('users', tables)
            self.assertIn('categories', tables)
            self.assertIn('expenses', tables)
            self.assertIn('budgets', tables)

            cat_cursor = db.execute("SELECT name FROM categories ORDER BY id")
            categories = [row['name'] for row in cat_cursor.fetchall()]
            self.assertEqual(len(categories), 8)
            expected = ['Food', 'Travel', 'Shopping', 'Bills', 'Entertainment', 'Health', 'Education', 'Other']
            self.assertEqual(categories, expected)

    def test_user_registration_success(self):
        """Verify valid user registration redirects to login."""
        response = self.client.post('/auth/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        self.assertIn(b'Welcome Back', response.data)

        # Verify user exists in database and password is not stored plaintext
        with self.app.app_context():
            user = get_user_by_email('test@example.com')
            self.assertIsNotNone(user)
            self.assertEqual(user['name'], 'Test User')
            self.assertNotEqual(user['password_hash'], 'password123')
            self.assertTrue(user['password_hash'].startswith('pbkdf2:sha256:'))

    def test_registration_validation_errors(self):
        """Verify validation errors for passwords mismatch, invalid email, short password."""
        # Mismatched passwords
        res = self.client.post('/auth/register', data={
            'name': 'Mismatch User',
            'email': 'mismatch@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', res.data)

        # Password too short (< 6 chars)
        res = self.client.post('/auth/register', data={
            'name': 'Short Pwd',
            'email': 'short@example.com',
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        self.assertIn(b'at least 6 characters', res.data)

        # Duplicate email
        self.client.post('/auth/register', data={
            'name': 'First User',
            'email': 'dup@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        res2 = self.client.post('/auth/register', data={
            'name': 'Second User',
            'email': 'dup@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'already exists', res2.data)

    def test_login_and_logout_flow(self):
        """Verify login with correct and incorrect credentials, and logout."""
        # First register
        self.client.post('/auth/register', data={
            'name': 'Login Tester',
            'email': 'login@example.com',
            'password': 'correct_password',
            'confirm_password': 'correct_password'
        })

        # Wrong password
        res_fail = self.client.post('/auth/login', data={
            'email': 'login@example.com',
            'password': 'wrong_password'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_fail.data)

        # Correct password
        res_ok = self.client.post('/auth/login', data={
            'email': 'login@example.com',
            'password': 'correct_password'
        }, follow_redirects=True)
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn(b'Welcome back, Login Tester!', res_ok.data)
        self.assertIn(b'Login Tester', res_ok.data)
        self.assertIn(b'Logout', res_ok.data)

        # Access protected route now that we are logged in
        res_dash = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(res_dash.status_code, 200)

        # Logout
        res_logout = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', res_logout.data)
        self.assertIn(b'Sign In', res_logout.data)

    def test_protected_route_blocks_unauthenticated_user(self):
        """Verify @login_required decorator redirects unauthenticated requests."""
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)
        self.assertIn(b'Welcome Back', response.data)


if __name__ == '__main__':
    unittest.main()
