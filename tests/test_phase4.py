"""
Phase 4 Verification Tests: Budget Management & Alert Engine
Tests budget setup, monthly spend aggregation, 80% warning triggers,
100% critical alerts, multi-tenant isolation, and month switching.
"""

import unittest
import os
import tempfile
from app import create_app
from utils.db import get_db, init_db
from utils.auth_helpers import create_user
from utils.expense_helpers import create_expense, get_categories
from utils.budget_helpers import (
    get_budgets_for_month,
    set_or_update_budget,
    delete_budget,
    get_active_alerts
)


class Phase4TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-phase4'
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            self.user1 = create_user('Budget User 1', 'user1@test.com', 'password123')
            self.user2 = create_user('Budget User 2', 'user2@test.com', 'password123')
            cats = get_categories()
            self.cat_food = next(c for c in cats if c['name'] == 'Food')
            self.cat_travel = next(c for c in cats if c['name'] == 'Travel')
            self.cat_bills = next(c for c in cats if c['name'] == 'Bills')

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def login(self, email='user1@test.com', password='password123'):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_budget_upsert_and_deletion(self):
        """Verify setting, updating, and deleting budget limits."""
        with self.app.app_context():
            # Set initial budget
            ok = set_or_update_budget(
                user_id=self.user1['id'],
                category_id=self.cat_food['id'],
                month='2026-10',
                limit_amount=5000.0
            )
            self.assertTrue(ok)

            data = get_budgets_for_month(self.user1['id'], '2026-10')
            food_item = next(i for i in data['items'] if i['category_name'] == 'Food')
            self.assertEqual(food_item['limit_amount'], 5000.0)

            # Update limit for same month (upsert)
            set_or_update_budget(
                user_id=self.user1['id'],
                category_id=self.cat_food['id'],
                month='2026-10',
                limit_amount=6000.0
            )
            data_updated = get_budgets_for_month(self.user1['id'], '2026-10')
            food_updated = next(i for i in data_updated['items'] if i['category_name'] == 'Food')
            self.assertEqual(food_updated['limit_amount'], 6000.0)

            # Delete budget
            b_id = food_updated['budget_id']
            del_ok = delete_budget(b_id, self.user1['id'])
            self.assertTrue(del_ok)

            data_after = get_budgets_for_month(self.user1['id'], '2026-10')
            food_after = next(i for i in data_after['items'] if i['category_name'] == 'Food')
            self.assertIsNone(food_after['limit_amount'])
            self.assertEqual(food_after['status'], 'unset')

    def test_threshold_alerts_normal_warning_exceeded(self):
        """Verify normal (<80%), warning (80-99%), and exceeded (>=100%) statuses."""
        with self.app.app_context():
            month = '2026-10'

            # Set budgets: Food = 1000, Travel = 1000, Bills = 1000
            set_or_update_budget(self.user1['id'], self.cat_food['id'], month, 1000.0)
            set_or_update_budget(self.user1['id'], self.cat_travel['id'], month, 1000.0)
            set_or_update_budget(self.user1['id'], self.cat_bills['id'], month, 1000.0)

            # Food: spend 500 (50% -> normal)
            create_expense(self.user1['id'], self.cat_food['id'], 500.0, '2026-10-05')

            # Travel: spend 850 (85% -> warning)
            create_expense(self.user1['id'], self.cat_travel['id'], 850.0, '2026-10-10')

            # Bills: spend 1200 (120% -> exceeded)
            create_expense(self.user1['id'], self.cat_bills['id'], 1200.0, '2026-10-15')

            data = get_budgets_for_month(self.user1['id'], month)
            items_by_cat = {i['category_name']: i for i in data['items']}

            # Food check (normal)
            food = items_by_cat['Food']
            self.assertEqual(food['status'], 'normal')
            self.assertEqual(food['percentage'], 50.0)
            self.assertEqual(food['remaining_amount'], 500.0)

            # Travel check (warning >= 80%)
            travel = items_by_cat['Travel']
            self.assertEqual(travel['status'], 'warning')
            self.assertEqual(travel['percentage'], 85.0)
            self.assertEqual(travel['remaining_amount'], 150.0)

            # Bills check (exceeded >= 100%)
            bills = items_by_cat['Bills']
            self.assertEqual(bills['status'], 'exceeded')
            self.assertEqual(bills['percentage'], 120.0)
            self.assertEqual(bills['overage_amount'], 200.0)

            # Active alerts check
            alerts = get_active_alerts(self.user1['id'], month)
            alert_cats = [a['category_name'] for a in alerts]
            self.assertIn('Travel', alert_cats)
            self.assertIn('Bills', alert_cats)
            self.assertNotIn('Food', alert_cats)

    def test_strict_multi_tenant_isolation(self):
        """Verify User 2 cannot see or manipulate User 1's budgets."""
        with self.app.app_context():
            set_or_update_budget(self.user1['id'], self.cat_food['id'], '2026-10', 4000.0)

            # User 2 checks budgets for 2026-10
            u2_data = get_budgets_for_month(self.user2['id'], '2026-10')
            u2_food = next(i for i in u2_data['items'] if i['category_name'] == 'Food')
            self.assertIsNone(u2_food['limit_amount'])

            # User 2 tries to delete User 1's budget
            u1_data = get_budgets_for_month(self.user1['id'], '2026-10')
            u1_b_id = next(i for i in u1_data['items'] if i['category_name'] == 'Food')['budget_id']
            del_attempt = delete_budget(u1_b_id, self.user2['id'])
            self.assertFalse(del_attempt)

            # User 1's budget still exists
            u1_after = get_budgets_for_month(self.user1['id'], '2026-10')
            self.assertIsNotNone(next(i for i in u1_after['items'] if i['category_name'] == 'Food')['limit_amount'])

    def test_month_boundary_isolation(self):
        """Verify expenses in month A do not affect budgets in month B."""
        with self.app.app_context():
            # Budget set for October and November
            set_or_update_budget(self.user1['id'], self.cat_food['id'], '2026-10', 1000.0)
            set_or_update_budget(self.user1['id'], self.cat_food['id'], '2026-11', 1000.0)

            # Expense logged in October only
            create_expense(self.user1['id'], self.cat_food['id'], 900.0, '2026-10-25')

            # October should be in warning (90%)
            oct_data = get_budgets_for_month(self.user1['id'], '2026-10')
            oct_food = next(i for i in oct_data['items'] if i['category_name'] == 'Food')
            self.assertEqual(oct_food['status'], 'warning')
            self.assertEqual(oct_food['spent_amount'], 900.0)

            # November should have 0 spent and be normal
            nov_data = get_budgets_for_month(self.user1['id'], '2026-11')
            nov_food = next(i for i in nov_data['items'] if i['category_name'] == 'Food')
            self.assertEqual(nov_food['status'], 'normal')
            self.assertEqual(nov_food['spent_amount'], 0.0)

    def test_web_routes_set_and_alerts_api(self):
        """Verify HTTP routes for setting budgets and fetching active alerts via JSON."""
        self.login('user1@test.com')

        # View budgets page
        res = self.client.get('/budgets?month=2026-10')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Budget Planner & Alerts', res.data)

        # Set budget via POST
        res_post = self.client.post('/budgets/set', data={
            'category_id': str(self.cat_food['id']),
            'month': '2026-10',
            'limit_amount': '2500'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b'Budget limit of \xe2\x82\xb92500.00 updated successfully', res_post.data)

        # Check API
        res_api = self.client.get('/budgets/api/alerts?month=2026-10')
        self.assertEqual(res_api.status_code, 200)
        json_data = res_api.get_json()
        self.assertTrue(json_data['success'])


if __name__ == '__main__':
    unittest.main()
