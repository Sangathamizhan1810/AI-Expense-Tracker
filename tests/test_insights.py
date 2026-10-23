"""
AI-Based Expense Tracker — Spending Insights Engine Tests
=========================================================
Tests for deterministic month-over-month calculation, plain-language
observations, actionable savings tips, and graceful new-user handling.
"""

import os
import tempfile
import unittest

from app import create_app
from utils.db import init_db, get_db
from utils.auth_helpers import create_user
from utils.expense_helpers import create_expense
from utils.budget_helpers import set_or_update_budget
from utils.insights_helpers import (
    get_month_over_month_summary,
    generate_spending_insights
)


class TestSpendingInsights(unittest.TestCase):
    """Test suite for deterministic spending insights engine."""

    def setUp(self):
        """Set up an isolated test database and test context."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True

        with self.app.app_context():
            init_db()
            db = get_db()
            cats = db.execute("SELECT id, name FROM categories").fetchall()
            self.cat_map = {c['name']: c['id'] for c in cats}

            u1 = create_user("Alice", "alice@example.com", "Password123")
            self.user1_id = u1['id']
            u2 = create_user("Bob", "bob@example.com", "Password123")
            self.user2_id = u2['id']

    def tearDown(self):
        """Clean up temporary test database."""
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    def test_new_user_insufficient_history(self):
        """INS-04: Graceful handling when no prior month data exists."""
        with self.app.app_context():
            # Current month expense only
            create_expense(self.user1_id, self.cat_map['Food'], 450.0, "2026-10-12", "Dinner")

            insights = generate_spending_insights(self.user1_id, "2026-10")

            self.assertFalse(insights['has_enough_data'])
            self.assertGreaterEqual(len(insights['observations']), 1)
            first_obs = insights['observations'][0]
            self.assertEqual(first_obs['title'], 'First Month Tracking')
            self.assertIn('₹450.00', first_obs['text'])

    def test_month_over_month_increase(self):
        """INS-01, INS-02: Detect total and category spending increases with exact percentages."""
        with self.app.app_context():
            # September 2026: 1000 total (Food 500, Travel 500)
            create_expense(self.user1_id, self.cat_map['Food'], 500.0, "2026-09-10")
            create_expense(self.user1_id, self.cat_map['Travel'], 500.0, "2026-09-15")

            # October 2026: 1500 total (Food 1000, Travel 500) -> +50% overall, Food +100%
            create_expense(self.user1_id, self.cat_map['Food'], 1000.0, "2026-10-05")
            create_expense(self.user1_id, self.cat_map['Travel'], 500.0, "2026-10-10")

            summary = get_month_over_month_summary(self.user1_id, "2026-10")
            self.assertEqual(summary['current_total'], 1500.0)
            self.assertEqual(summary['prev_total'], 1000.0)
            self.assertEqual(summary['delta_amount'], 500.0)
            self.assertEqual(summary['delta_percentage'], 50.0)

            # Check insights
            insights = generate_spending_insights(self.user1_id, "2026-10")
            self.assertTrue(insights['has_enough_data'])
            obs_texts = " ".join([o['text'] for o in insights['observations']])
            self.assertIn("50.0% higher", obs_texts)
            self.assertIn("Food spending is 100.0% higher", obs_texts)

    def test_month_over_month_decrease_and_savings_win(self):
        """INS-01, INS-02: Recognize spending drop and savings win."""
        with self.app.app_context():
            # September: 2000 in Shopping
            create_expense(self.user1_id, self.cat_map['Shopping'], 2000.0, "2026-09-05")

            # October: 1000 in Shopping -> -50%
            create_expense(self.user1_id, self.cat_map['Shopping'], 1000.0, "2026-10-05")

            insights = generate_spending_insights(self.user1_id, "2026-10")
            self.assertTrue(insights['has_enough_data'])

            obs_texts = " ".join([o['text'] for o in insights['observations']])
            self.assertIn("50.0% lower", obs_texts)
            self.assertIn("Shopping spending dropped by 50.0%", obs_texts)

    def test_budget_driven_actionable_savings_tips(self):
        """INS-03: Generate high-priority recommendations for exceeded/warning budgets."""
        with self.app.app_context():
            # Set budget of 1000 for Entertainment
            set_or_update_budget(self.user1_id, self.cat_map['Entertainment'], "2026-10", 1000.0)
            # Spend 1250 (exceeded by 250)
            create_expense(self.user1_id, self.cat_map['Entertainment'], 1250.0, "2026-10-10")

            insights = generate_spending_insights(self.user1_id, "2026-10")
            self.assertTrue(len(insights['savings_tips']) > 0)

            high_tips = [t for t in insights['savings_tips'] if t['priority'] == 'high']
            self.assertEqual(len(high_tips), 1)
            self.assertIn('Entertainment Budget Exceeded', high_tips[0]['title'])
            self.assertIn('₹250.00', high_tips[0]['text'])

    def test_insights_strict_user_isolation(self):
        """Verify complete user isolation in insights generation."""
        with self.app.app_context():
            # User 1 has no expenses
            # User 2 logs a large expense
            create_expense(self.user2_id, self.cat_map['Bills'], 9999.0, "2026-10-01")

            u1_summary = get_month_over_month_summary(self.user1_id, "2026-10")
            self.assertEqual(u1_summary['current_total'], 0.0)
            self.assertEqual(u1_summary['prev_total'], 0.0)

            u1_insights = generate_spending_insights(self.user1_id, "2026-10")
            self.assertFalse(u1_insights['has_enough_data'])
            self.assertNotIn('9999', str(u1_insights))


if __name__ == '__main__':
    unittest.main()
