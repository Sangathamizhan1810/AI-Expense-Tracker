"""
AI-Based Expense Tracker — Analytics Helper Module
===================================================
Aggregates financial KPIs, category distributions, historical spending trends,
and budget-vs-actual metrics with strict user data isolation.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta

from utils.db import get_db

# Canonical Category Styling Tokens
CATEGORY_META = {
    'Food': {'color': '#10b981', 'icon': '🍔'},
    'Travel': {'color': '#3b82f6', 'icon': '✈️'},
    'Shopping': {'color': '#ec4899', 'icon': '🛍️'},
    'Bills': {'color': '#ef4444', 'icon': '📄'},
    'Entertainment': {'color': '#8b5cf6', 'icon': '🎬'},
    'Health': {'color': '#06b6d4', 'icon': '💊'},
    'Education': {'color': '#f59e0b', 'icon': '📚'},
    'Other': {'color': '#64748b', 'icon': '📦'},
}


def _normalize_month(month=None):
    """Normalize or default a month string to YYYY-MM."""
    if not month:
        return datetime.now().strftime('%Y-%m')
    try:
        # Validate format
        dt = datetime.strptime(month.strip(), '%Y-%m')
        return dt.strftime('%Y-%m')
    except (ValueError, AttributeError):
        return datetime.now().strftime('%Y-%m')


def get_monthly_kpis(user_id, month=None):
    """
    Calculate high-level financial summary KPIs for a user and month.
    
    Returns:
        dict: {
            'month': 'YYYY-MM',
            'month_label': 'October 2026',
            'total_spent': float,
            'expense_count': int,
            'total_budget': float,
            'active_budgets_count': int,
            'budget_remaining': float,
            'budget_utilization': float,
            'top_category': dict or None { 'name', 'amount', 'percentage', 'color', 'icon' },
            'is_over_budget': bool
        }
    """
    db = get_db()
    month = _normalize_month(month)
    dt = datetime.strptime(month, '%Y-%m')
    month_label = dt.strftime('%B %Y')

    # 1. Total spend and transaction count
    spend_row = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0.0) AS total_spent, COUNT(id) AS expense_count
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        """,
        (user_id, month)
    ).fetchone()

    total_spent = float(spend_row['total_spent']) if spend_row else 0.0
    expense_count = int(spend_row['expense_count']) if spend_row else 0

    # 2. Total budget limit and active budget count
    budget_row = db.execute(
        """
        SELECT COALESCE(SUM(limit_amount), 0.0) AS total_budget, COUNT(id) AS budget_count
        FROM budgets
        WHERE user_id = ? AND month = ?
        """,
        (user_id, month)
    ).fetchone()

    total_budget = float(budget_row['total_budget']) if budget_row else 0.0
    active_budgets_count = int(budget_row['budget_count']) if budget_row else 0

    # 3. Remaining capacity & utilization
    if total_budget > 0:
        budget_remaining = round(total_budget - total_spent, 2)
        budget_utilization = round((total_spent / total_budget) * 100, 1)
        is_over_budget = total_spent > total_budget
    else:
        budget_remaining = 0.0
        budget_utilization = 0.0
        is_over_budget = False

    # 4. Top spending category
    top_row = db.execute(
        """
        SELECT c.id, c.name, COALESCE(SUM(e.amount), 0.0) AS cat_spend
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.id
        HAVING cat_spend > 0
        ORDER BY cat_spend DESC
        LIMIT 1
        """,
        (user_id, month)
    ).fetchone()

    top_category = None
    if top_row and total_spent > 0:
        cat_name = top_row['name']
        cat_spend = float(top_row['cat_spend'])
        cat_meta = CATEGORY_META.get(cat_name, {'color': '#64748b', 'icon': '🏷️'})
        top_category = {
            'name': cat_name,
            'amount': round(cat_spend, 2),
            'percentage': round((cat_spend / total_spent) * 100, 1),
            'color': cat_meta['color'],
            'icon': cat_meta['icon']
        }

    return {
        'month': month,
        'month_label': month_label,
        'total_spent': round(total_spent, 2),
        'expense_count': expense_count,
        'total_budget': round(total_budget, 2),
        'active_budgets_count': active_budgets_count,
        'budget_remaining': budget_remaining,
        'budget_utilization': budget_utilization,
        'top_category': top_category,
        'is_over_budget': is_over_budget
    }


def get_category_distribution(user_id, month=None):
    """
    Get aggregated spending breakdown per category for Chart.js Donut/Pie.
    
    Returns:
        dict: {
            'labels': list of str,
            'amounts': list of float,
            'percentages': list of float,
            'colors': list of hex colors,
            'icons': list of str,
            'total_spent': float
        }
    """
    db = get_db()
    month = _normalize_month(month)

    rows = db.execute(
        """
        SELECT c.name, COALESCE(SUM(e.amount), 0.0) AS cat_amount
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.id
        HAVING cat_amount > 0
        ORDER BY cat_amount DESC
        """,
        (user_id, month)
    ).fetchall()

    labels = []
    amounts = []
    colors = []
    icons = []
    total_spent = sum(float(r['cat_amount']) for r in rows)

    for r in rows:
        name = r['name']
        amt = round(float(r['cat_amount']), 2)
        meta = CATEGORY_META.get(name, {'color': '#64748b', 'icon': '🏷️'})
        labels.append(name)
        amounts.append(amt)
        colors.append(meta['color'])
        icons.append(meta['icon'])

    percentages = [
        round((amt / total_spent) * 100, 1) if total_spent > 0 else 0.0
        for amt in amounts
    ]

    return {
        'labels': labels,
        'amounts': amounts,
        'percentages': percentages,
        'colors': colors,
        'icons': icons,
        'total_spent': round(total_spent, 2)
    }


def get_spending_trends(user_id, months_count=6, reference_month=None):
    """
    Calculate spending trends for the past N consecutive months up to reference_month.
    
    Returns:
        dict: {
            'months': list of readable month labels (e.g. ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']),
            'keys': list of YYYY-MM strings,
            'amounts': list of floats
        }
    """
    db = get_db()
    ref_month_str = _normalize_month(reference_month)
    ref_dt = datetime.strptime(ref_month_str, '%Y-%m')

    # Generate list of past N months in chronological order
    month_keys = []
    month_labels = []
    for i in range(months_count - 1, -1, -1):
        target_dt = ref_dt - relativedelta(months=i)
        month_keys.append(target_dt.strftime('%Y-%m'))
        # If trend spans different years, show 'May 25', otherwise 'May'
        month_labels.append(target_dt.strftime('%b %y'))

    # Query amounts for all months in list
    placeholders = ','.join('?' for _ in month_keys)
    query = f"""
        SELECT strftime('%Y-%m', expense_date) AS m, COALESCE(SUM(amount), 0.0) AS amt
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) IN ({placeholders})
        GROUP BY m
    """
    params = [user_id] + month_keys
    rows = db.execute(query, params).fetchall()

    spend_map = {r['m']: round(float(r['amt']), 2) for r in rows}
    amounts = [spend_map.get(m, 0.0) for m in month_keys]

    return {
        'months': month_labels,
        'keys': month_keys,
        'amounts': amounts
    }


def get_budget_vs_actual(user_id, month=None):
    """
    Compare allocated monthly budget limits against actual spend per category.
    
    Returns:
        dict: {
            'categories': list of category names,
            'budget_amounts': list of floats,
            'actual_amounts': list of floats,
            'percentages': list of floats,
            'colors': list of hex colors,
            'has_data': bool
        }
    """
    db = get_db()
    month = _normalize_month(month)

    rows = db.execute(
        """
        SELECT 
            c.name,
            COALESCE(b.limit_amount, 0.0) AS budget_limit,
            COALESCE((
                SELECT SUM(e.amount)
                FROM expenses e
                WHERE e.user_id = ?
                  AND e.category_id = c.id
                  AND strftime('%Y-%m', e.expense_date) = ?
            ), 0.0) AS actual_spend
        FROM categories c
        LEFT JOIN budgets b 
          ON b.category_id = c.id 
         AND b.user_id = ? 
         AND b.month = ?
        ORDER BY c.name ASC
        """,
        (user_id, month, user_id, month)
    ).fetchall()

    categories = []
    budget_amounts = []
    actual_amounts = []
    percentages = []
    colors = []

    # Filter to categories that have either a budget or actual spend
    active_rows = [r for r in rows if float(r['budget_limit']) > 0 or float(r['actual_spend']) > 0]

    # If no categories have budgets or spend, show all categories with 0
    display_rows = active_rows if active_rows else rows

    for r in display_rows:
        name = r['name']
        b_limit = round(float(r['budget_limit']), 2)
        a_spend = round(float(r['actual_spend']), 2)
        pct = round((a_spend / b_limit) * 100, 1) if b_limit > 0 else (100.0 if a_spend > 0 else 0.0)
        meta = CATEGORY_META.get(name, {'color': '#64748b', 'icon': '🏷️'})

        categories.append(name)
        budget_amounts.append(b_limit)
        actual_amounts.append(a_spend)
        percentages.append(pct)
        colors.append(meta['color'])

    has_data = any(b > 0 or a > 0 for b, a in zip(budget_amounts, actual_amounts))

    return {
        'categories': categories,
        'budget_amounts': budget_amounts,
        'actual_amounts': actual_amounts,
        'percentages': percentages,
        'colors': colors,
        'has_data': has_data
    }


def get_full_dashboard_payload(user_id, month=None):
    """
    Convenience method aggregating all analytics data for a given month.
    """
    month = _normalize_month(month)
    return {
        'kpis': get_monthly_kpis(user_id, month),
        'category_distribution': get_category_distribution(user_id, month),
        'spending_trends': get_spending_trends(user_id, 6, month),
        'budget_vs_actual': get_budget_vs_actual(user_id, month)
    }
