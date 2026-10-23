"""
Phase 2 Verification Tests: Core Expense Management & Export
Verifies expense CRUD, strict multi-tenant isolation, filtering, summary statistics, and CSV export.
"""

import unittest
import os
import tempfile
import io
import csv
from app import create_app
from utils.db import get_db, init_db
from utils.auth_helpers import create_user
from utils.expense_helpers import (
    create_expense,
    get_expense_by_id,
    update_expense,
    delete_expense,
    get_expenses,
    get_expenses_summary,
    get_categories
)


class Phase2TestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['DATABASE'] = self.db_path
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-phase2'
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db()
            # Create two test users for data isolation testing
            self.user1 = create_user('Alice', 'alice@test.com', 'password123')
            self.user2 = create_user('Bob', 'bob@test.com', 'password123')
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

    def login(self, email, password='password123'):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_expense_crud_helpers(self):
        """Verify create, get, update, delete expense helper functions."""
        with self.app.app_context():
            # Create
            exp_id = create_expense(
                user_id=self.user1['id'],
                category_id=self.cat_food['id'],
                amount=250.75,
                expense_date='2026-10-15',
                note='Swiggy dinner'
            )
            self.assertIsNotNone(exp_id)

            # Retrieve
            exp = get_expense_by_id(exp_id, self.user1['id'])
            self.assertIsNotNone(exp)
            self.assertEqual(exp['amount'], 250.75)
            self.assertEqual(exp['category_name'], 'Food')
            self.assertEqual(exp['note'], 'Swiggy dinner')

            # Update
            updated = update_expense(
                expense_id=exp_id,
                user_id=self.user1['id'],
                category_id=self.cat_travel['id'],
                amount=300.0,
                expense_date='2026-10-16',
                note='Uber ride'
            )
            self.assertTrue(updated)
            exp_after = get_expense_by_id(exp_id, self.user1['id'])
            self.assertEqual(exp_after['amount'], 300.0)
            self.assertEqual(exp_after['category_name'], 'Travel')

            # Delete
            deleted = delete_expense(exp_id, self.user1['id'])
            self.assertTrue(deleted)
            self.assertIsNone(get_expense_by_id(exp_id, self.user1['id']))

    def test_expense_validation_errors(self):
        """Verify invalid amounts, missing categories, and bad dates are rejected."""
        with self.app.app_context():
            # Negative amount
            with self.assertRaises(ValueError):
                create_expense(self.user1['id'], self.cat_food['id'], -50, '2026-10-15')

            # Zero amount
            with self.assertRaises(ValueError):
                create_expense(self.user1['id'], self.cat_food['id'], 0, '2026-10-15')

            # Non-existent category
            with self.assertRaises(ValueError):
                create_expense(self.user1['id'], 99999, 100, '2026-10-15')

            # Invalid date format
            with self.assertRaises(ValueError):
                create_expense(self.user1['id'], self.cat_food['id'], 100, 'not-a-date')

    def test_strict_multi_tenant_data_isolation(self):
        """Verify User 2 cannot access, edit, or delete User 1's records."""
        with self.app.app_context():
            # Alice creates an expense
            alice_exp_id = create_expense(
                user_id=self.user1['id'],
                category_id=self.cat_food['id'],
                amount=500.0,
                expense_date='2026-10-10',
                note="Alice's private dinner"
            )

            # Bob tries to read it
            bob_fetch = get_expense_by_id(alice_exp_id, self.user2['id'])
            self.assertIsNone(bob_fetch)

            # Bob tries to update it
            bob_update = update_expense(
                expense_id=alice_exp_id,
                user_id=self.user2['id'],
                category_id=self.cat_bills['id'],
                amount=1.0,
                expense_date='2026-10-10'
            )
            self.assertFalse(bob_update)

            # Bob tries to delete it
            bob_delete = delete_expense(alice_exp_id, self.user2['id'])
            self.assertFalse(bob_delete)

            # Expense still belongs untouched to Alice
            alice_fetch = get_expense_by_id(alice_exp_id, self.user1['id'])
            self.assertIsNotNone(alice_fetch)
            self.assertEqual(alice_fetch['amount'], 500.0)

    def test_web_routes_add_edit_delete(self):
        """Verify web routes for adding, editing, and deleting expenses through browser client."""
        self.login('alice@test.com')

        # Add expense via POST
        res_add = self.client.post('/expenses/add', data={
            'amount': '420.50',
            'category_id': str(self.cat_food['id']),
            'expense_date': '2026-10-20',
            'note': 'Groceries from Zepto'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b'Expense of \xe2\x82\xb9420.50 added successfully', res_add.data)
        self.assertIn(b'Groceries from Zepto', res_add.data)

        # Get the ID of created expense
        with self.app.app_context():
            expenses = get_expenses(self.user1['id'])
            self.assertEqual(len(expenses), 1)
            exp_id = expenses[0]['id']

        # Edit via POST
        res_edit = self.client.post(f'/expenses/{exp_id}/edit', data={
            'amount': '450.00',
            'category_id': str(self.cat_food['id']),
            'expense_date': '2026-10-21',
            'note': 'Zepto + fruits'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'Expense updated successfully', res_edit.data)
        self.assertIn(b'Zepto + fruits', res_edit.data)
        self.assertIn(b'450.00', res_edit.data)

        # Delete via POST
        res_del = self.client.post(f'/expenses/{exp_id}/delete', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b'Expense deleted successfully', res_del.data)

        with self.app.app_context():
            self.assertEqual(len(get_expenses(self.user1['id'])), 0)

    def test_filtering_and_summary_math(self):
        """Verify multi-criteria filtering by category, date range, and summary aggregation."""
        with self.app.app_context():
            # Add 3 expenses for Alice
            create_expense(self.user1['id'], self.cat_food['id'], 200.0, '2026-10-01')
            create_expense(self.user1['id'], self.cat_food['id'], 300.0, '2026-10-15')
            create_expense(self.user1['id'], self.cat_travel['id'], 500.0, '2026-10-20')

            # Unfiltered summary
            summary_all = get_expenses_summary(self.user1['id'])
            self.assertEqual(summary_all['total_count'], 3)
            self.assertEqual(summary_all['total_amount'], 1000.0)

            # Filtered by Food category
            summary_food = get_expenses_summary(self.user1['id'], category_id=self.cat_food['id'])
            self.assertEqual(summary_food['total_count'], 2)
            self.assertEqual(summary_food['total_amount'], 500.0)

            # Filtered by Date Range (2026-10-10 to 2026-10-25)
            filtered_dates = get_expenses(
                self.user1['id'],
                start_date='2026-10-10',
                end_date='2026-10-25'
            )
            self.assertEqual(len(filtered_dates), 2)
            summary_dates = get_expenses_summary(
                self.user1['id'],
                start_date='2026-10-10',
                end_date='2026-10-25'
            )
            self.assertEqual(summary_dates['total_count'], 2)
            self.assertEqual(summary_dates['total_amount'], 800.0)

    def test_csv_export(self):
        """Verify CSV export endpoint returns valid formatted CSV with user data."""
        with self.app.app_context():
            create_expense(self.user1['id'], self.cat_food['id'], 150.0, '2026-10-05', 'Quick lunch')
            create_expense(self.user1['id'], self.cat_travel['id'], 75.0, '2026-10-06', 'Metro ticket')

        self.login('alice@test.com')
        response = self.client.get('/expenses/export')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.headers.get('Content-Type', ''))
        self.assertIn('attachment; filename="expenses_', response.headers.get('Content-Disposition', ''))

        # Parse CSV output
        csv_text = response.data.decode('utf-8')
        reader = list(csv.reader(io.StringIO(csv_text)))
        self.assertEqual(reader[0], ['Expense ID', 'Date', 'Category', 'Amount (INR)', 'Note', 'Logged At'])
        self.assertEqual(len(reader), 3)  # header + 2 expenses
        self.assertEqual(reader[1][2], 'Travel')
        self.assertEqual(reader[1][3], '75.00')
        self.assertEqual(reader[2][2], 'Food')
        self.assertEqual(reader[2][3], '150.00')


if __name__ == '__main__':
    unittest.main()
