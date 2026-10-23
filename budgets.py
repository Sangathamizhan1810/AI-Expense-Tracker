"""
AI-Based Expense Tracker — Budgets Blueprint
============================================
Handles monthly spending limits, real-time threshold calculations,
80% warnings, and 100% overspending alert notifications.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from utils.budget_helpers import (
    get_budgets_for_month,
    set_or_update_budget,
    delete_budget,
    get_active_alerts,
    normalize_month
)
from utils.expense_helpers import get_categories

budgets_bp = Blueprint('budgets', __name__, url_prefix='/budgets')


@budgets_bp.before_request
def require_login():
    """Ensure user is authenticated before accessing budget endpoints."""
    if g.user is None:
        flash('Please log in to manage your budgets.', 'error')
        return redirect(url_for('auth.login', next=request.path))


@budgets_bp.route('', strict_slashes=False)
@budgets_bp.route('/', strict_slashes=False)
def index():
    """View monthly budget health, category limits, progress bars, and alerts."""
    month = request.args.get('month')
    user_id = g.user['id']

    budget_data = get_budgets_for_month(user_id, month)
    categories = get_categories()
    active_alerts = get_active_alerts(user_id, budget_data['month'])

    return render_template(
        'budgets/index.html',
        month=budget_data['month'],
        items=budget_data['items'],
        summary=budget_data['summary'],
        categories=categories,
        alerts=active_alerts
    )


@budgets_bp.route('/set', methods=['POST'])
def set_budget():
    """Create or update a category budget limit for a specific month."""
    category_id = request.form.get('category_id')
    month = request.form.get('month')
    limit_amount = request.form.get('limit_amount')
    user_id = g.user['id']

    target_month = normalize_month(month)

    try:
        set_or_update_budget(user_id, category_id, target_month, limit_amount)
        flash(f'Budget limit of ₹{float(limit_amount):.2f} updated successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash('Failed to update budget limit. Please try again.', 'error')

    return redirect(url_for('budgets.index', month=target_month))


@budgets_bp.route('/<int:id>/delete', methods=['POST'])
def remove_budget(id):
    """Delete a budget limit."""
    month = request.form.get('month') or request.args.get('month')
    target_month = normalize_month(month)
    user_id = g.user['id']

    deleted = delete_budget(id, user_id)
    if deleted:
        flash('Budget limit removed successfully.', 'success')
    else:
        flash('Budget not found or unauthorized access.', 'error')

    return redirect(url_for('budgets.index', month=target_month))


@budgets_bp.route('/api/alerts')
def api_alerts():
    """Fetch active alerts as JSON for client-side indicators."""
    month = request.args.get('month')
    user_id = g.user['id']
    alerts = get_active_alerts(user_id, month)
    return jsonify({
        'success': True,
        'count': len(alerts),
        'alerts': alerts
    })
