"""
AI-Based Expense Tracker — Phase 5 Test Suite
=============================================
Automated verification for Interactive Visual Analytics Dashboard:
- KPI calculations (DASH-01)
- Category distribution aggregation (DASH-02)
- 6-month historical spending trend (DASH-03)
- Budget vs. Actual comparison (DASH-04)
- User isolation and endpoint authorization
"""

import os
import tempfile
import unittest

from app import create_app
from utils.db import init_db, get_db
from utils.auth_helpers import create_user
from utils.expense_helpers import create_expense
from utils.budget_helpers import set_or_update_budget
from utils.analytics_helpers import (
    get_monthly_kpis,
    get_category_distribution,
    get_spending_trends,
    get_budget_vs_actual,
    get_full_dashboard_payload
)


class TestPhase5Dashboard(unittest.TestCase):
    """Test suite for Phase 5 Analytics Dashboard."""

    def setUp(self):
        """Set up an isolated test database and Flask test client."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            db = get_db()
            # Retrieve category map: name -> id
            cats = db.execute("SELECT id, name FROM categories").fetchall()
            self.cat_map = {c['name']: c['id'] for c in cats}

            # Create test user 1
            u1 = create_user("Alice", "alice@example.com", "Password123")
            self.user1_id = u1['id']
            # Create test user 2 (for isolation testing)
            u2 = create_user("Bob", "bob@example.com", "Password123")
            self.user2_id = u2['id']

    def tearDown(self):
        """Clean up temporary database file."""
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    def test_kpis_calculation_with_expenses_and_budgets(self):
        """DASH-01: Verify total spend, budget, remaining, utilization, and top category."""
        with self.app.app_context():
            # Add expenses for user 1 in 2026-10
            create_expense(self.user1_id, self.cat_map['Food'], 600.0, "2026-10-05", "Groceries")
            create_expense(self.user1_id, self.cat_map['Travel'], 400.0, "2026-10-10", "Uber")

            # Set budgets for user 1 in 2026-10
            set_or_update_budget(self.user1_id, self.cat_map['Food'], "2026-10", 1000.0)
            set_or_update_budget(self.user1_id, self.cat_map['Travel'], "2026-10", 500.0)

            kpis = get_monthly_kpis(self.user1_id, "2026-10")

            self.assertEqual(kpis['total_spent'], 1000.0)
            self.assertEqual(kpis['expense_count'], 2)
            self.assertEqual(kpis['total_budget'], 1500.0)
            self.assertEqual(kpis['active_budgets_count'], 2)
            self.assertEqual(kpis['budget_remaining'], 500.0)
            self.assertAlmostEqual(kpis['budget_utilization'], 66.7, places=1)
            self.assertFalse(kpis['is_over_budget'])

            # Top category should be Food (600 out of 1000 = 60.0%)
            self.assertIsNotNone(kpis['top_category'])
            self.assertEqual(kpis['top_category']['name'], 'Food')
            self.assertEqual(kpis['top_category']['amount'], 600.0)
            self.assertEqual(kpis['top_category']['percentage'], 60.0)

    def test_kpis_empty_month(self):
        """DASH-01: Graceful handling of a month with zero records."""
        with self.app.app_context():
            kpis = get_monthly_kpis(self.user1_id, "2024-01")

            self.assertEqual(kpis['total_spent'], 0.0)
            self.assertEqual(kpis['expense_count'], 0)
            self.assertEqual(kpis['total_budget'], 0.0)
            self.assertEqual(kpis['active_budgets_count'], 0)
            self.assertEqual(kpis['budget_remaining'], 0.0)
            self.assertEqual(kpis['budget_utilization'], 0.0)
            self.assertIsNone(kpis['top_category'])
            self.assertFalse(kpis['is_over_budget'])

    def test_kpis_over_budget(self):
        """DASH-01: Detect over-budget status when spending exceeds limits."""
        with self.app.app_context():
            create_expense(self.user1_id, self.cat_map['Bills'], 2500.0, "2026-10-15", "Rent")
            set_or_update_budget(self.user1_id, self.cat_map['Bills'], "2026-10", 2000.0)

            kpis = get_monthly_kpis(self.user1_id, "2026-10")
            self.assertEqual(kpis['total_spent'], 2500.0)
            self.assertEqual(kpis['total_budget'], 2000.0)
            self.assertEqual(kpis['budget_remaining'], -500.0)
            self.assertTrue(kpis['is_over_budget'])
            self.assertEqual(kpis['budget_utilization'], 125.0)

    def test_category_distribution_donut(self):
        """DASH-02: Verify category percentage breakdown for Donut chart."""
        with self.app.app_context():
            create_expense(self.user1_id, self.cat_map['Food'], 300.0, "2026-10-02")
            create_expense(self.user1_id, self.cat_map['Shopping'], 700.0, "2026-10-08")

            dist = get_category_distribution(self.user1_id, "2026-10")

            self.assertEqual(dist['total_spent'], 1000.0)
            self.assertIn('Shopping', dist['labels'])
            self.assertIn('Food', dist['labels'])

            # Shopping should be 70% and Food 30%
            shop_idx = dist['labels'].index('Shopping')
            food_idx = dist['labels'].index('Food')
            self.assertEqual(dist['percentages'][shop_idx], 70.0)
            self.assertEqual(dist['percentages'][food_idx], 30.0)
            self.assertEqual(sum(dist['percentages']), 100.0)

    def test_spending_trends_6_months(self):
        """DASH-03: Verify 6-month historical trajectory line chart data."""
        with self.app.app_context():
            # Add expenses in Aug, Sep, Oct 2026
            create_expense(self.user1_id, self.cat_map['Food'], 200.0, "2026-08-10")
            create_expense(self.user1_id, self.cat_map['Travel'], 500.0, "2026-09-15")
            create_expense(self.user1_id, self.cat_map['Bills'], 800.0, "2026-10-20")

            trends = get_spending_trends(self.user1_id, 6, "2026-10")

            self.assertEqual(len(trends['months']), 6)
            self.assertEqual(len(trends['keys']), 6)
            self.assertEqual(len(trends['amounts']), 6)

            # Last key should be 2026-10 with 800.0
            self.assertEqual(trends['keys'][-1], '2026-10')
            self.assertEqual(trends['amounts'][-1], 800.0)

            # 2nd to last should be 2026-09 with 500.0
            self.assertEqual(trends['keys'][-2], '2026-09')
            self.assertEqual(trends['amounts'][-2], 500.0)

            # 3rd to last should be 2026-08 with 200.0
            self.assertEqual(trends['keys'][-3], '2026-08')
            self.assertEqual(trends['amounts'][-3], 200.0)

    def test_budget_vs_actual_bar_chart(self):
        """DASH-04: Verify side-by-side budget limit vs actual spend comparison."""
        with self.app.app_context():
            set_or_update_budget(self.user1_id, self.cat_map['Entertainment'], "2026-10", 1500.0)
            create_expense(self.user1_id, self.cat_map['Entertainment'], 1200.0, "2026-10-12")

            bva = get_budget_vs_actual(self.user1_id, "2026-10")

            self.assertTrue(bva['has_data'])
            self.assertIn('Entertainment', bva['categories'])

            idx = bva['categories'].index('Entertainment')
            self.assertEqual(bva['budget_amounts'][idx], 1500.0)
            self.assertEqual(bva['actual_amounts'][idx], 1200.0)

    def test_dashboard_routes_and_user_isolation(self):
        """Verify authentication, HTML rendering, JSON API, and complete user isolation."""
        # 1. Unauthenticated request redirects to login
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        # 2. Authenticate as User 1
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.user1_id

        with self.app.app_context():
            create_expense(self.user1_id, self.cat_map['Food'], 999.0, "2026-10-01", "User1 Food")
            # User 2 logs an expense
            create_expense(self.user2_id, self.cat_map['Food'], 8888.0, "2026-10-01", "User2 Luxury")

        # HTML route
        res = self.client.get('/dashboard?month=2026-10')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('Financial Analytics', html)
        self.assertIn('categoryDonutChart', html)
        self.assertIn('trendLineChart', html)
        self.assertIn('budgetBarChart', html)
        self.assertIn('₹999.00', html)
        # Verify User 2's spend is NOT leaked to User 1
        self.assertNotIn('₹8888.00', html)

        # JSON API route
        api_res = self.client.get('/dashboard/api/analytics?month=2026-10')
        self.assertEqual(api_res.status_code, 200)
        json_data = api_res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['data']['kpis']['total_spent'], 999.0)


if __name__ == '__main__':
    unittest.main()
