"""
AI-Based Expense Tracker — Phase 6 Comprehensive UAT Suite
===========================================================
End-to-end verification covering all 13 standardized test cases
specified for the AI-Based Information System mini-project:
- TC-01: User Registration with valid credentials
- TC-02: User Registration invalid input rejection
- TC-03: User Login success & session establishment
- TC-04: User Login rejection on invalid password
- TC-05: Manual Expense Creation with full fields
- TC-06: Expense Validation constraints
- TC-07: Expense Filtering and RFC 4180 CSV export
- TC-08: AI Natural Language Expense Parsing & amount extraction
- TC-09: AI Classifier Fallback on low confidence / unknown input
- TC-10: Monthly Budget Allocation & Atomic Upsert
- TC-11: Budget Warning (80%) and Overspending (100%) alerts
- TC-12: Visual Analytics Dashboard KPIs & Chart aggregations
- TC-13: Spending Insights Engine (Month-over-month & recommendations)
"""

import io
import os
import tempfile
import unittest
from werkzeug.security import check_password_hash

from app import create_app
from utils.db import init_db, get_db
from utils.auth_helpers import create_user, get_user_by_email
from utils.expense_helpers import (
    create_expense,
    get_expense_by_id,
    get_expenses,
    validate_expense_data
)
from utils.nlp_parser import parse_expense_sentence, extract_amount
from utils.nlp_classifier import predict_category
from utils.budget_helpers import set_or_update_budget, get_budgets_for_month
from utils.analytics_helpers import get_full_dashboard_payload
from utils.insights_helpers import generate_spending_insights


class TestSystemUAT13Cases(unittest.TestCase):
    """Complete 13-Case End-to-End System Test Suite."""

    def setUp(self):
        """Set up isolated test database and test client."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            db = get_db()
            cats = db.execute("SELECT id, name FROM categories").fetchall()
            self.cat_map = {c['name']: c['id'] for c in cats}

    def tearDown(self):
        """Clean up temporary database file."""
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    # ── TC-01: User Registration with Valid Credentials ──────────────────
    def test_tc01_user_registration_valid(self):
        """TC-01: User can register successfully; password is encrypted with pbkdf2:sha256."""
        res = self.client.post('/auth/register', data={
            'name': 'Rahul Sharma',
            'email': 'rahul@example.com',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123'
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        with self.app.app_context():
            user = get_user_by_email('rahul@example.com')
            self.assertIsNotNone(user)
            self.assertEqual(user['name'], 'Rahul Sharma')
            # Verify password hash
            self.assertNotEqual(user['password_hash'], 'SecurePassword123')
            self.assertTrue(check_password_hash(user['password_hash'], 'SecurePassword123'))

    # ── TC-02: User Registration Input Rejection ─────────────────────────
    def test_tc02_user_registration_invalid(self):
        """TC-02: Registration fails on short password or duplicate email."""
        # Short password (< 6 chars)
        res = self.client.post('/auth/register', data={
            'name': 'Short Pass',
            'email': 'short@example.com',
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        self.assertIn('at least 6 characters', res.data.decode('utf-8'))

        # Duplicate email
        with self.app.app_context():
            create_user("First User", "duplicate@example.com", "Password123")

        res_dup = self.client.post('/auth/register', data={
            'name': 'Second User',
            'email': 'duplicate@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertIn('already exists', res_dup.data.decode('utf-8'))

    # ── TC-03: User Login Success ────────────────────────────────────────
    def test_tc03_user_login_success(self):
        """TC-03: Registered user can log in; establishes session and redirects to dashboard."""
        with self.app.app_context():
            create_user("Priya Verma", "priya@example.com", "MySecretKey99")

        res = self.client.post('/auth/login', data={
            'email': 'priya@example.com',
            'password': 'MySecretKey99'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn('Financial Analytics', res.data.decode('utf-8'))

    # ── TC-04: User Login Failure on Wrong Password ──────────────────────
    def test_tc04_user_login_failure(self):
        """TC-04: System rejects login with incorrect credentials."""
        with self.app.app_context():
            create_user("Arjun", "arjun@example.com", "CorrectPassword1")

        res = self.client.post('/auth/login', data={
            'email': 'arjun@example.com',
            'password': 'WrongPassword99'
        }, follow_redirects=True)

        self.assertIn('Invalid email or password', res.data.decode('utf-8'))

    # ── TC-05: Manual Expense Creation ───────────────────────────────────
    def test_tc05_manual_expense_creation(self):
        """TC-05: User can manually record an expense with amount, category, date, and note."""
        with self.app.app_context():
            user = create_user("Aditi", "aditi@example.com", "Password123")
            user_id = user['id']

            exp_id = create_expense(
                user_id=user_id,
                category_id=self.cat_map['Shopping'],
                amount=1499.50,
                expense_date="2026-10-15",
                note="Zara shirt"
            )

            exp = get_expense_by_id(exp_id, user_id)
            self.assertIsNotNone(exp)
            self.assertEqual(exp['amount'], 1499.50)
            self.assertEqual(exp['category_name'], 'Shopping')
            self.assertEqual(exp['note'], 'Zara shirt')

    # ── TC-06: Expense Input Validation Constraints ──────────────────────
    def test_tc06_expense_validation(self):
        """TC-06: System rejects negative amount, non-existent category, or bad date format."""
        with self.app.app_context():
            # Negative amount
            with self.assertRaises(ValueError):
                validate_expense_data(-50, self.cat_map['Food'], "2026-10-01")

            # Zero amount
            with self.assertRaises(ValueError):
                validate_expense_data(0, self.cat_map['Food'], "2026-10-01")

            # Non-existent category
            with self.assertRaises(ValueError):
                validate_expense_data(100, 999999, "2026-10-01")

            # Malformed date
            with self.assertRaises(ValueError):
                validate_expense_data(100, self.cat_map['Food'], "invalid-date")

    # ── TC-07: Expense Filtering and CSV Export ──────────────────────────
    def test_tc07_expense_filtering_and_csv_export(self):
        """TC-07: Filter expenses by category and export valid RFC 4180 CSV."""
        with self.app.app_context():
            user = create_user("Kavita", "kavita@example.com", "Password123")
            user_id = user['id']

            create_expense(user_id, self.cat_map['Food'], 300.0, "2026-10-02", "Lunch")
            create_expense(user_id, self.cat_map['Travel'], 500.0, "2026-10-05", "Metro")

            # Filter by Food
            food_items = get_expenses(user_id, category_id=self.cat_map['Food'])
            self.assertEqual(len(food_items), 1)
            self.assertEqual(food_items[0]['category_name'], 'Food')

        # Export CSV via endpoint
        with self.client.session_transaction() as sess:
            sess['user_id'] = user_id

        res = self.client.get('/expenses/export')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.headers['Content-Type'])
        csv_text = res.data.decode('utf-8')
        self.assertIn("Expense ID,Date,Category,Amount (INR),Note,Logged At", csv_text)
        self.assertIn("Food", csv_text)
        self.assertIn("Travel", csv_text)
        self.assertIn("300.00", csv_text)

    # ── TC-08: AI NLP Sentence Parsing & ₹ Extraction ────────────────────
    def test_tc08_ai_expense_nlp_parsing(self):
        """TC-08: Offline NLP engine extracts ₹ amount and predicts category accurately."""
        with self.app.app_context():
            # Test sentence: "Dinner at Haldiram for 450"
            parsed = parse_expense_sentence("Dinner at Haldiram for 450")
            self.assertEqual(parsed['amount'], 450.0)
            self.assertEqual(parsed['category_name'], 'Food')
            self.assertGreater(parsed['confidence'], 0.5)

            # Test sentence with rupee symbol: "₹350 uber ride"
            parsed_uber = parse_expense_sentence("₹350 uber ride")
            self.assertEqual(parsed_uber['amount'], 350.0)
            self.assertEqual(parsed_uber['category_name'], 'Travel')

    # ── TC-09: AI Classifier Fallback Handling ───────────────────────────
    def test_tc09_ai_classifier_fallback(self):
        """TC-09: Unknown/ambiguous text falls back to 'Other' or provides valid prediction."""
        with self.app.app_context():
            parsed = parse_expense_sentence("Random gibberish xyzabc 120")
            self.assertEqual(parsed['amount'], 120.0)
            self.assertIsNotNone(parsed['category_name'])

    # ── TC-10: Monthly Budget Allocation & Atomic Upsert ─────────────────
    def test_tc10_monthly_budget_allocation(self):
        """TC-10: Budget limits are allocated and atomic upserts handle changes seamlessly."""
        with self.app.app_context():
            user = create_user("Manish", "manish@example.com", "Password123")
            user_id = user['id']

            # Set initial budget of 2000 for Food in 2026-10
            set_or_update_budget(user_id, self.cat_map['Food'], "2026-10", 2000.0)
            budgets = get_budgets_for_month(user_id, "2026-10")
            food_b = [b for b in budgets['items'] if b['category_name'] == 'Food'][0]
            self.assertEqual(food_b['limit_amount'], 2000.0)

            # Update budget to 3000 (atomic upsert)
            set_or_update_budget(user_id, self.cat_map['Food'], "2026-10", 3000.0)
            budgets_updated = get_budgets_for_month(user_id, "2026-10")
            food_b2 = [b for b in budgets_updated['items'] if b['category_name'] == 'Food'][0]
            self.assertEqual(food_b2['limit_amount'], 3000.0)

    # ── TC-11: Budget Warning & Critical Alerts ───────────────────────────
    def test_tc11_budget_alert_thresholds(self):
        """TC-11: Triggers warning status at >= 80% and exceeded status at >= 100%."""
        with self.app.app_context():
            user = create_user("Sneha", "sneha@example.com", "Password123")
            user_id = user['id']

            # Set 1000 limit for Food
            set_or_update_budget(user_id, self.cat_map['Food'], "2026-10", 1000.0)

            # Spend 850 (85% -> warning)
            create_expense(user_id, self.cat_map['Food'], 850.0, "2026-10-05")
            b_status = get_budgets_for_month(user_id, "2026-10")
            food_b = [b for b in b_status['items'] if b['category_name'] == 'Food'][0]
            self.assertEqual(food_b['status'], 'warning')

            # Spend another 200 (Total 1050 / 1000 = 105% -> exceeded)
            create_expense(user_id, self.cat_map['Food'], 200.0, "2026-10-10")
            b_status2 = get_budgets_for_month(user_id, "2026-10")
            food_b2 = [b for b in b_status2['items'] if b['category_name'] == 'Food'][0]
            self.assertEqual(food_b2['status'], 'exceeded')
            self.assertEqual(food_b2['overage_amount'], 50.0)

    # ── TC-12: Visual Analytics Dashboard Metrics & Visualizations ────────
    def test_tc12_analytics_dashboard_metrics(self):
        """TC-12: Full analytics payload generates valid KPI, donut, trend line, and bar chart data."""
        with self.app.app_context():
            user = create_user("Vikram", "vikram@example.com", "Password123")
            user_id = user['id']

            create_expense(user_id, self.cat_map['Food'], 400.0, "2026-10-01")
            create_expense(user_id, self.cat_map['Travel'], 600.0, "2026-10-02")
            set_or_update_budget(user_id, self.cat_map['Travel'], "2026-10", 800.0)

            payload = get_full_dashboard_payload(user_id, "2026-10")

            # 1. KPIs
            self.assertEqual(payload['kpis']['total_spent'], 1000.0)
            self.assertEqual(payload['kpis']['top_category']['name'], 'Travel')

            # 2. Donut breakdown
            self.assertEqual(len(payload['category_distribution']['labels']), 2)
            self.assertEqual(sum(payload['category_distribution']['percentages']), 100.0)

            # 3. 6-Month trends
            self.assertEqual(len(payload['spending_trends']['months']), 6)

            # 4. Budget vs actual
            self.assertTrue(payload['budget_vs_actual']['has_data'])

    # ── TC-13: Spending Insights Engine ───────────────────────────────────
    def test_tc13_spending_insights_engine(self):
        """TC-13: Deterministic month-over-month observations and actionable recommendations."""
        with self.app.app_context():
            user = create_user("Ananya", "ananya@example.com", "Password123")
            user_id = user['id']

            # Prior month: September (Food 1000)
            create_expense(user_id, self.cat_map['Food'], 1000.0, "2026-09-10")

            # Current month: October (Food 1500 -> +50% increase)
            create_expense(user_id, self.cat_map['Food'], 1500.0, "2026-10-10")
            set_or_update_budget(user_id, self.cat_map['Food'], "2026-10", 1200.0)  # exceeded by 300

            insights = generate_spending_insights(user_id, "2026-10")

            self.assertTrue(insights['has_enough_data'])
            # Verify observations
            obs_joined = " ".join([o['text'] for o in insights['observations']])
            self.assertIn("50.0% higher", obs_joined)

            # Verify budget recommendation
            tip_joined = " ".join([t['text'] for t in insights['savings_tips']])
            self.assertIn("Food has surpassed your monthly limit by ₹300.00", tip_joined)


if __name__ == '__main__':
    unittest.main()
