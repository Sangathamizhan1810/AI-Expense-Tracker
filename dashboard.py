"""
AI-Based Expense Tracker — Dashboard Blueprint
===============================================
Delivers visual financial analytics, category distributions,
monthly spending trends, and budget vs actual comparisons with Chart.js.
"""

import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, g

from utils.auth_helpers import login_required
from utils.analytics_helpers import get_full_dashboard_payload

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('', strict_slashes=False)
@dashboard_bp.route('/', strict_slashes=False)
@login_required
def index():
    """
    Render visual analytics dashboard with pre-calculated financial KPIs
    and pre-injected JSON state for instant Chart.js rendering.
    """
    user_id = g.user['id']
    month = request.args.get('month', '').strip()
    if not month:
        month = datetime.now().strftime('%Y-%m')

    payload = get_full_dashboard_payload(user_id, month)

    return render_template(
        'dashboard/index.html',
        month=month,
        kpis=payload['kpis'],
        category_distribution=payload['category_distribution'],
        spending_trends=payload['spending_trends'],
        budget_vs_actual=payload['budget_vs_actual'],
        dashboard_json=json.dumps(payload)
    )


@dashboard_bp.route('/api/analytics', methods=['GET'])
@login_required
def api_analytics():
    """
    JSON API endpoint returning full analytics payload for a given month.
    Supports dynamic AJAX calendar switching without page reload.
    """
    user_id = g.user['id']
    month = request.args.get('month', '').strip()
    if not month:
        month = datetime.now().strftime('%Y-%m')

    payload = get_full_dashboard_payload(user_id, month)
    return jsonify({
        'success': True,
        'data': payload
    })
