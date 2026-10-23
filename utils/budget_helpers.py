"""
Budget Helpers Module
=====================
Handles monthly category budget persistence, real-time expense summation,
utilization percentage computation, and 80%/100% threshold alert detection.
"""

from datetime import datetime
import re
from utils.db import get_db

MONTH_REGEX = re.compile(r'^\d{4}-(?:0[1-9]|1[0-2])$')


def normalize_month(month_str=None):
    """
    Ensure month is in valid YYYY-MM format.
    Defaults to current calendar month if None or invalid.
    """
    if not month_str:
        return datetime.now().strftime('%Y-%m')
    month_str = str(month_str).strip()
    if MONTH_REGEX.match(month_str):
        return month_str
    return datetime.now().strftime('%Y-%m')


def get_budgets_for_month(user_id, month=None):
    """
    Calculate budget status and real-time spending for all 8 categories for a given month.
    Enforces strict user isolation (WHERE user_id = ?).
    """
    target_month = normalize_month(month)
    db = get_db()

    # 1. Fetch all categories
    cats = db.execute("SELECT id, name FROM categories ORDER BY name ASC").fetchall()

    # 2. Fetch existing budget limits for user and target month
    budget_rows = db.execute(
        """
        SELECT id, category_id, limit_amount
        FROM budgets
        WHERE user_id = ? AND month = ?
        """,
        (user_id, target_month)
    ).fetchall()
    budgets_by_cat = {row['category_id']: row for row in budget_rows}

    # 3. Sum expenses for user in target month grouped by category
    expense_rows = db.execute(
        """
        SELECT category_id, COALESCE(SUM(amount), 0.0) AS total_spent
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY category_id
        """,
        (user_id, target_month)
    ).fetchall()
    spent_by_cat = {row['category_id']: float(row['total_spent']) for row in expense_rows}

    items = []
    total_budget = 0.0
    total_spent = 0.0
    warning_count = 0
    exceeded_count = 0

    for cat in cats:
        cid = cat['id']
        cname = cat['name']

        b_entry = budgets_by_cat.get(cid)
        spent = round(spent_by_cat.get(cid, 0.0), 2)
        total_spent += spent

        if b_entry:
            budget_id = b_entry['id']
            limit_amount = round(float(b_entry['limit_amount']), 2)
            total_budget += limit_amount
            remaining = round(limit_amount - spent, 2)
            overage = round(max(0.0, spent - limit_amount), 2)
            pct = round((spent / limit_amount) * 100.0, 1) if limit_amount > 0 else 0.0

            if pct >= 100.0:
                status = 'exceeded'
                exceeded_count += 1
            elif pct >= 80.0:
                status = 'warning'
                warning_count += 1
            else:
                status = 'normal'
        else:
            budget_id = None
            limit_amount = None
            remaining = None
            overage = 0.0
            pct = 0.0
            status = 'unset'

        items.append({
            'category_id': cid,
            'category_name': cname,
            'budget_id': budget_id,
            'limit_amount': limit_amount,
            'spent_amount': spent,
            'remaining_amount': remaining,
            'overage_amount': overage,
            'percentage': pct,
            'status': status
        })

    total_remaining = round(total_budget - total_spent, 2) if total_budget > 0 else 0.0
    overall_pct = round((total_spent / total_budget) * 100.0, 1) if total_budget > 0 else 0.0

    return {
        'month': target_month,
        'items': items,
        'summary': {
            'total_budget': round(total_budget, 2),
            'total_spent': round(total_spent, 2),
            'total_remaining': total_remaining,
            'overall_percentage': overall_pct,
            'configured_count': len(budget_rows),
            'warning_count': warning_count,
            'exceeded_count': exceeded_count
        }
    }


def set_or_update_budget(user_id, category_id, month, limit_amount):
    """
    Set or update a monthly spending limit for a category.
    Performs an atomic upsert on (user_id, category_id, month).
    """
    target_month = normalize_month(month)

    try:
        float_limit = round(float(limit_amount), 2)
        if float_limit <= 0:
            raise ValueError("Budget limit must be greater than 0.")
    except (ValueError, TypeError):
        raise ValueError("Please provide a valid positive budget amount.")

    db = get_db()

    # Verify category exists
    cat = db.execute("SELECT id FROM categories WHERE id = ?", (category_id,)).fetchone()
    if not cat:
        raise ValueError("Selected category does not exist.")

    # SQLite upsert
    db.execute(
        """
        INSERT INTO budgets (user_id, category_id, month, limit_amount)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, category_id, month)
        DO UPDATE SET limit_amount = excluded.limit_amount
        """,
        (user_id, int(category_id), target_month, float_limit)
    )
    db.commit()
    return True


def delete_budget(budget_id, user_id):
    """
    Delete a budget record strictly matching id and user_id.
    """
    db = get_db()
    cursor = db.execute(
        "DELETE FROM budgets WHERE id = ? AND user_id = ?",
        (budget_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def get_active_alerts(user_id, month=None):
    """
    Retrieve active budget alerts (warning >= 80% and critical >= 100%)
    for a user in the specified month.
    """
    budget_data = get_budgets_for_month(user_id, month)
    alerts = []
    for item in budget_data['items']:
        if item['status'] in ('warning', 'exceeded'):
            alerts.append(item)
    return alerts
