"""
Phase 3 Verification Tests: NLP & Machine Learning Categorization
Tests regex amount extraction, natural language sentence parsing,
AI Quick-Add endpoints, and user isolation.
"""

import unittest
import os
import tempfile
from unittest.mock import patch
from app import create_app
from utils.db import get_db, init_db
from utils.auth_helpers import create_user
from utils.nlp_parser import extract_amount, parse_expense_sentence
from utils.expense_helpers import get_expenses


class Phase3TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-phase3'
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            self.user = create_user('Test NLP User', 'nlp@test.com', 'password123')

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def login(self, email='nlp@test.com', password='password123'):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_regex_amount_extraction(self):
        """Verify regex extraction across various Indian currency and sentence formats."""
        cases = [
            ("Swiggy 250", 250.0, "swiggy"),
            ("metro recharge 50", 50.0, "metro recharge"),
            ("₹500 petrol", 500.0, "petrol"),
            ("rs 350 grocery", 350.0, "grocery"),
            ("rs. 45.50 coffee", 45.5, "coffee"),
            ("auto 40 rs", 40.0, "auto"),
            ("movie ticket 350 rupees", 350.0, "movie ticket"),
            ("paid 1200 for electricity bill", 1200.0, "paid for electricity bill"),
            ("lunch buffet without amount", None, "lunch buffet without amount")
        ]

        for text, expected_amt, expected_keyword in cases:
            amt, desc = extract_amount(text)
            self.assertEqual(amt, expected_amt, f"Amount failed for: {text}")
            self.assertIn(expected_keyword.lower(), desc.lower(), f"Description failed for: {text}")

    def test_sentence_parsing_with_ml(self):
        """Verify parse_expense_sentence integrates regex and ML classification correctly."""
        with self.app.app_context():
            parsed_food = parse_expense_sentence("Swiggy chicken biryani 320")
            self.assertEqual(parsed_food['amount'], 320.0)
            self.assertEqual(parsed_food['category_name'], 'Food')
            self.assertGreaterEqual(parsed_food['confidence'], 0.50)
            self.assertFalse(parsed_food['is_low_confidence'])

            parsed_travel = parse_expense_sentence("Uber to airport 450")
            self.assertEqual(parsed_travel['amount'], 450.0)
            self.assertEqual(parsed_travel['category_name'], 'Travel')

            parsed_bills = parse_expense_sentence("Bescom electricity bill 1200")
            self.assertEqual(parsed_bills['amount'], 1200.0)
            self.assertEqual(parsed_bills['category_name'], 'Bills')

    def test_ai_parse_endpoint(self):
        """Verify POST /expenses/ai-parse returns parsed JSON payload."""
        self.login()
        res = self.client.post('/expenses/ai-parse', json={
            'sentence': 'Zomato pizza 499'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        parsed = data['parsed']
        self.assertEqual(parsed['amount'], 499.0)
        self.assertEqual(parsed['category_name'], 'Food')
        self.assertGreaterEqual(parsed['confidence'], 0.50)

    def test_ai_quick_add_success(self):
        """Verify POST /expenses/ai-quick-add persists new transaction in database."""
        self.login()
        res = self.client.post('/expenses/ai-quick-add', data={
            'sentence': 'Airtel broadband wifi 999'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI Quick-Add: Recorded', res.data)
        self.assertIn(b'999.00', res.data)
        self.assertIn(b'Bills', res.data)

        # Check DB record
        with self.app.app_context():
            expenses = get_expenses(self.user['id'])
            self.assertEqual(len(expenses), 1)
            self.assertEqual(expenses[0]['amount'], 999.0)
            self.assertEqual(expenses[0]['category_name'], 'Bills')

    def test_ai_quick_add_with_category_override(self):
        """Verify user can manually override the predicted category when submitting."""
        self.login()
        # "chai 30" predicts Food, but user overrides to "Other" (e.g., category_id=8)
        with self.app.app_context():
            db = get_db()
            other_id = db.execute("SELECT id FROM categories WHERE name = 'Other'").fetchone()['id']

        res = self.client.post('/expenses/ai-quick-add', data={
            'sentence': 'chai 30',
            'category_id': str(other_id)
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            expenses = get_expenses(self.user['id'])
            self.assertEqual(len(expenses), 1)
            self.assertEqual(expenses[0]['category_name'], 'Other')
    def test_ai_quick_add_missing_amount_redirects_to_form(self):
        """Verify input without amount redirects gracefully to pre-filled add form."""
        self.login()
        res = self.client.post('/expenses/ai-quick-add', data={
            'sentence': 'just regular lunch'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Could not automatically detect an amount', res.data)
        self.assertIn(b'Add New Expense', res.data)

    def test_ai_parse_gemini_quota_exceeded_fallback(self):
        """Verify that when Gemini quota limit is exceeded (HTTP 429), it flags quota_exceeded and falls back to offline model."""
        self.login()
        with patch('utils.nlp_parser.classify_with_gemini', return_value=(None, True)):
            res = self.client.post('/expenses/ai-parse', json={
                'sentence': 'Zomato biriyani 350',
                'prefer_gemini': True
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            parsed = data['parsed']
            self.assertTrue(parsed['quota_exceeded'])
            self.assertIn('limit is over', parsed['warning_notice'])
            self.assertEqual(parsed['model_source'], 'offline_nlp')
            self.assertEqual(parsed['category_name'], 'Food')
            self.assertEqual(parsed['amount'], 350.0)

    def test_ai_parse_gemini_success(self):
        """Verify that when Gemini responds successfully, it uses Gemini AI classification."""
        self.login()
        gemini_mock_response = {
            'amount': 450.0,
            'category': 'Travel',
            'description': 'Rapido bike taxi',
            'confidence': 0.98,
            'source': 'gemini_ai'
        }
        with patch('utils.nlp_parser.classify_with_gemini', return_value=(gemini_mock_response, False)):
            res = self.client.post('/expenses/ai-parse', json={
                'sentence': 'rapido 450 bike ride',
                'prefer_gemini': True
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            parsed = data['parsed']
            self.assertFalse(parsed['quota_exceeded'])
            self.assertEqual(parsed['model_source'], 'gemini_ai')
            self.assertEqual(parsed['category_name'], 'Travel')
            self.assertEqual(parsed['amount'], 450.0)
            self.assertEqual(parsed['description'], 'Rapido bike taxi')


if __name__ == '__main__':
    unittest.main()
