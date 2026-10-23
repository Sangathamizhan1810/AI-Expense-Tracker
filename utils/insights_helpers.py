"""
AI-Based Expense Tracker — Spending Insights Engine
===================================================
Generates deterministic, rule-based financial insights and actionable savings
recommendations based on month-over-month spending comparisons and budget utilization.
Zero hallucinations: all math is calculated deterministically in Python/SQL.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta

from utils.db import get_db
from utils.analytics_helpers import CATEGORY_META, _normalize_month


def get_month_over_month_summary(user_id, month=None):
    """
    Compute total spend and per-category spend for current month (M)
    and previous month (M-1) with strict user isolation (WHERE user_id = ?).

    Returns:
        dict: {
            'month': 'YYYY-MM',
            'month_label': 'October 2026',
            'prev_month': 'YYYY-MM',
            'prev_month_label': 'September 2026',
            'current_total': float,
            'prev_total': float,
            'delta_amount': float,
            'delta_percentage': float or None,
            'categories': dict of category_name -> {
                'current': float,
                'prev': float,
                'delta_amount': float,
                'delta_percentage': float or None,
                'status': 'increased' | 'decreased' | 'same' | 'new' | 'zero'
            }
        }
    """
    db = get_db()
    current_month_str = _normalize_month(month)
    current_dt = datetime.strptime(current_month_str, '%Y-%m')
    prev_dt = current_dt - relativedelta(months=1)
    prev_month_str = prev_dt.strftime('%Y-%m')

    current_label = current_dt.strftime('%B %Y')
    prev_label = prev_dt.strftime('%B %Y')

    # Fetch all categories
    cats = db.execute("SELECT id, name FROM categories ORDER BY name ASC").fetchall()

    # Query current month spend per category
    curr_rows = db.execute(
        """
        SELECT category_id, COALESCE(SUM(amount), 0.0) AS cat_spend
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY category_id
        """,
        (user_id, current_month_str)
    ).fetchall()
    curr_map = {r['category_id']: round(float(r['cat_spend']), 2) for r in curr_rows}

    # Query previous month spend per category
    prev_rows = db.execute(
        """
        SELECT category_id, COALESCE(SUM(amount), 0.0) AS cat_spend
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY category_id
        """,
        (user_id, prev_month_str)
    ).fetchall()
    prev_map = {r['category_id']: round(float(r['cat_spend']), 2) for r in prev_rows}

    current_total = round(sum(curr_map.values()), 2)
    prev_total = round(sum(prev_map.values()), 2)

    delta_amount = round(current_total - prev_total, 2)
    if prev_total > 0:
        delta_percentage = round((delta_amount / prev_total) * 100.0, 1)
    else:
        delta_percentage = None

    categories_summary = {}
    for cat in cats:
        cid = cat['id']
        cname = cat['name']
        c_amt = curr_map.get(cid, 0.0)
        p_amt = prev_map.get(cid, 0.0)
        c_delta = round(c_amt - p_amt, 2)

        if p_amt > 0:
            c_pct = round((c_delta / p_amt) * 100.0, 1)
        else:
            c_pct = None

        if c_amt > 0 and p_amt == 0:
            status = 'new'
        elif c_amt == 0 and p_amt == 0:
            status = 'zero'
        elif c_delta > 0:
            status = 'increased'
        elif c_delta < 0:
            status = 'decreased'
        else:
            status = 'same'

        categories_summary[cname] = {
            'category_id': cid,
            'current': c_amt,
            'prev': p_amt,
            'delta_amount': c_delta,
            'delta_percentage': c_pct,
            'status': status
        }

    return {
        'month': current_month_str,
        'month_label': current_label,
        'prev_month': prev_month_str,
        'prev_month_label': prev_label,
        'current_total': current_total,
        'prev_total': prev_total,
        'delta_amount': delta_amount,
        'delta_percentage': delta_percentage,
        'categories': categories_summary
    }


def generate_spending_insights(user_id, month=None):
    """
    Generate up to 3 plain-language observations and actionable savings tips
    grounded strictly in mathematical calculation.
    """
    summary = get_month_over_month_summary(user_id, month)
    curr_total = summary['current_total']
    prev_total = summary['prev_total']
    curr_label = summary['month_label']
    prev_label = summary['prev_month_label']
    categories = summary['categories']

    observations = []
    savings_tips = []

    # Check for sufficient historical data (INS-04)
    has_enough_data = prev_total > 0

    if not has_enough_data:
        # Graceful empty/new user state
        if curr_total > 0:
            observations.append({
                'type': 'summary',
                'icon': '🌱',
                'title': 'First Month Tracking',
                'text': f"You have logged ₹{curr_total:,.2f} in expenses for {curr_label}. Full month-over-month spending comparisons will activate next month!"
            })
        else:
            observations.append({
                'type': 'summary',
                'icon': '📊',
                'title': 'No Activity Recorded',
                'text': f"No expenses have been recorded for {curr_label}. Log expenses to view automated spending insights."
            })
    else:
        # 1. Total Spend Observation (INS-01, INS-02)
        delta_amt = summary['delta_amount']
        delta_pct = summary['delta_percentage']

        if delta_amt > 0:
            observations.append({
                'type': 'increase',
                'icon': '📈',
                'title': 'Overall Spend Increase',
                'text': f"Total spending is {delta_pct}% higher than {prev_label} (₹{curr_total:,.2f} vs ₹{prev_total:,.2f})."
            })
        elif delta_amt < 0:
            observations.append({
                'type': 'decrease',
                'icon': '📉',
                'title': 'Spending Reduction',
                'text': f"Total spending is {abs(delta_pct)}% lower than {prev_label} (₹{curr_total:,.2f} vs ₹{prev_total:,.2f}). Great job!"
            })
        else:
            observations.append({
                'type': 'neutral',
                'icon': '⚖️',
                'title': 'Identical Spending',
                'text': f"Total spending is exactly equal to {prev_label} at ₹{curr_total:,.2f}."
            })

        # 2. Significant Category Increase Observation
        increased_cats = [
            (cname, info) for cname, info in categories.items()
            if info['status'] == 'increased' and info['delta_percentage'] is not None
        ]
        # Sort by percentage increase descending
        increased_cats.sort(key=lambda x: x[1]['delta_percentage'], reverse=True)

        if increased_cats:
            top_inc_name, top_inc_info = increased_cats[0]
            cat_meta = CATEGORY_META.get(top_inc_name, {'icon': '🏷️'})
            observations.append({
                'type': 'category_increase',
                'icon': cat_meta['icon'],
                'title': f'{top_inc_name} Surge',
                'text': f"{top_inc_name} spending is {top_inc_info['delta_percentage']}% higher than last month (₹{top_inc_info['current']:,.2f} vs ₹{top_inc_info['prev']:,.2f})."
            })
        else:
            # Check for new category spend
            new_cats = [
                (cname, info) for cname, info in categories.items()
                if info['status'] == 'new' and info['current'] > 0
            ]
            if new_cats:
                new_cats.sort(key=lambda x: x[1]['current'], reverse=True)
                top_new_name, top_new_info = new_cats[0]
                cat_meta = CATEGORY_META.get(top_new_name, {'icon': '🏷️'})
                observations.append({
                    'type': 'new_category',
                    'icon': cat_meta['icon'],
                    'title': f'New Category Activity',
                    'text': f"New expenses recorded in {top_new_name} this month: ₹{top_new_info['current']:,.2f}."
                })

        # 3. Category Savings Win Observation
        decreased_cats = [
            (cname, info) for cname, info in categories.items()
            if info['status'] == 'decreased' and info['delta_percentage'] is not None
        ]
        decreased_cats.sort(key=lambda x: x[1]['delta_percentage'])  # most negative first

        if decreased_cats and len(observations) < 3:
            top_dec_name, top_dec_info = decreased_cats[0]
            cat_meta = CATEGORY_META.get(top_dec_name, {'icon': '🏷️'})
            observations.append({
                'type': 'category_decrease',
                'icon': '🎉',
                'title': f'{top_dec_name} Savings Win',
                'text': f"Well done! {top_dec_name} spending dropped by {abs(top_dec_info['delta_percentage'])}% (₹{top_dec_info['current']:,.2f} vs ₹{top_dec_info['prev']:,.2f})."
            })

    # Ensure max 3 observations (INS-02)
    observations = observations[:3]

    # 4. Actionable Savings Recommendations (INS-03)
    db = get_db()
    current_month_str = summary['month']

    # Fetch budget limits and current spend for current month
    budget_rows = db.execute(
        """
        SELECT 
            c.name,
            b.limit_amount,
            COALESCE((
                SELECT SUM(e.amount) 
                FROM expenses e 
                WHERE e.user_id = ? AND e.category_id = c.id AND strftime('%Y-%m', e.expense_date) = ?
            ), 0.0) AS spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = ? AND b.month = ?
        """,
        (user_id, current_month_str, user_id, current_month_str)
    ).fetchall()

    exceeded_budgets = []
    warning_budgets = []

    for r in budget_rows:
        limit = float(r['limit_amount'])
        spent = float(r['spent'])
        if limit > 0:
            if spent >= limit:
                exceeded_budgets.append((r['name'], spent, limit, round(spent - limit, 2)))
            elif spent >= 0.8 * limit:
                pct = round((spent / limit) * 100.0, 1)
                warning_budgets.append((r['name'], spent, limit, pct))

    # Priority 1: Exceeded budget warnings
    for name, spent, limit, overage in exceeded_budgets:
        cat_meta = CATEGORY_META.get(name, {'icon': '⚠️'})
        savings_tips.append({
            'priority': 'high',
            'icon': '🚨',
            'title': f'{name} Budget Exceeded',
            'text': f"{name} has surpassed your monthly limit by ₹{overage:,.2f} (₹{spent:,.2f} / ₹{limit:,.2f}). Pause non-essential purchases in this category."
        })

    # Priority 2: 80% Threshold Warnings
    for name, spent, limit, pct in warning_budgets:
        cat_meta = CATEGORY_META.get(name, {'icon': '⚠️'})
        savings_tips.append({
            'priority': 'medium',
            'icon': '⚠️',
            'title': f'{name} Approaching Limit',
            'text': f"{name} spending has reached {pct}% of your ₹{limit:,.2f} limit (₹{spent:,.2f} spent). Monitor upcoming expenses carefully."
        })

    # Priority 3: Discretionary category tips
    # Find highest discretionary spend category (Food, Shopping, Entertainment)
    discretionary = ['Shopping', 'Food', 'Entertainment']
    disc_spends = [
        (cname, categories[cname]['current'])
        for cname in discretionary
        if cname in categories and categories[cname]['current'] > 0
    ]
    disc_spends.sort(key=lambda x: x[1], reverse=True)

    if disc_spends and len(savings_tips) < 3:
        top_disc_name, top_disc_amt = disc_spends[0]
        if top_disc_name == 'Food' and curr_total > 0:
            food_pct = round((top_disc_amt / curr_total) * 100.0, 1)
            savings_tips.append({
                'priority': 'tip',
                'icon': '💡',
                'title': 'Meal Planning Strategy',
                'text': f"Food represents {food_pct}% of your spending this month (₹{top_disc_amt:,.2f}). Preparing meals at home 2-3 days a week could save ~₹{round(top_disc_amt * 0.25, 0):,.0f}."
            })
        elif top_disc_name == 'Shopping' and curr_total > 0:
            savings_tips.append({
                'priority': 'tip',
                'icon': '💡',
                'title': '48-Hour Impulse Rule',
                'text': f"Shopping spending is at ₹{top_disc_amt:,.2f}. Try waiting 48 hours before purchasing non-essential items to avoid impulsive buying."
            })
        elif top_disc_name == 'Entertainment' and curr_total > 0:
            savings_tips.append({
                'priority': 'tip',
                'icon': '💡',
                'title': 'Subscription Audit',
                'text': f"Entertainment spending is ₹{top_disc_amt:,.2f}. Review active monthly streaming and app subscriptions for services you haven't used recently."
            })

    # Fallback general tip if no tips generated yet
    if not savings_tips:
        if curr_total > 0:
            savings_tips.append({
                'priority': 'tip',
                'icon': '🎯',
                'title': 'Set Monthly Budgets',
                'text': "Configure monthly category spending limits under the Budgets tab to receive proactive overspending alerts and personalized savings strategies."
            })
        else:
            savings_tips.append({
                'priority': 'tip',
                'icon': '🪄',
                'title': 'Quick Expense Entry',
                'text': "Use the AI Quick-Add field on the Expenses page to quickly log transactions by simply typing e.g. 'Lunch with friends 350'."
            })

    # Limit to top 3 tips
    savings_tips = savings_tips[:3]

    return {
        'has_enough_data': has_enough_data,
        'month': current_month_str,
        'month_label': curr_label,
        'prev_month': summary['prev_month'],
        'prev_month_label': prev_label,
        'observations': observations,
        'savings_tips': savings_tips
    }
