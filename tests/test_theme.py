"""
Theme System Verification Tests
Tests zero-FOUC resolver, dual-theme tokens, toggle button presence, and reactive event hooks.
"""

import unittest
import os
import tempfile
from app import create_app
from utils.db import init_db
from utils.auth_helpers import create_user


class ThemeSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            create_user('Theme Tester', 'theme@example.com', 'password123')

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_public_page_theme_elements(self):
        """Verify landing page includes zero-FOUC script and public toggle button."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')

        # Zero-FOUC script must be present in head
        self.assertIn('expenseai_theme', content)
        self.assertIn("document.documentElement.setAttribute('data-theme', savedTheme);", content)

        # Public theme toggle button and SVGs must be present
        self.assertIn('id="public-theme-toggle-btn"', content)
        self.assertIn('theme-toggle-icon--moon', content)
        self.assertIn('theme-toggle-icon--sun', content)

    def test_authenticated_page_theme_elements(self):
        """Verify authenticated app-topbar includes desktop theme toggle button."""
        # Log in
        self.client.post('/auth/login', data={
            'email': 'theme@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        content = response.data.decode('utf-8')

        # Authenticated topbar toggle button must be present
        self.assertIn('id="theme-toggle-btn"', content)
        self.assertIn('js-theme-toggle', content)
        self.assertIn('theme-toggle-icon--moon', content)
        self.assertIn('theme-toggle-icon--sun', content)

    def test_stylesheet_daylight_tokens(self):
        """Verify style.css defines [data-theme='light'] tokens and toggle button styles."""
        css_path = os.path.join(self.app.root_path, 'static', 'css', 'style.css')
        self.assertTrue(os.path.exists(css_path))
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()

        self.assertIn('[data-theme="light"]', css)
        self.assertIn('--bg-primary: #f8fafc', css)
        self.assertIn('--bg-surface: #ffffff', css)
        self.assertIn('--text-primary: #090d16', css)
        self.assertIn('.theme-toggle-btn', css)
        self.assertIn('.theme-toggle-icon--sun', css)

    def test_scripts_theme_integration(self):
        """Verify main.js and dashboard.js handle theme persistence and reactive sync."""
        main_js_path = os.path.join(self.app.root_path, 'static', 'js', 'main.js')
        dashboard_js_path = os.path.join(self.app.root_path, 'static', 'js', 'dashboard.js')

        with open(main_js_path, 'r', encoding='utf-8') as f:
            main_js = f.read()
        self.assertIn('js-theme-toggle', main_js)
        self.assertIn('expenseai_theme', main_js)
        self.assertIn("dispatchEvent(new CustomEvent('themechange'", main_js)

        with open(dashboard_js_path, 'r', encoding='utf-8') as f:
            dash_js = f.read()
        self.assertIn("window.addEventListener('themechange'", dash_js)
        self.assertIn('getThemeColors', dash_js)
