"""
AI-Based Expense Tracker — Expenses Blueprint
=============================================
Handles expense CRUD operations, tabular viewing, multi-criteria filtering,
and CSV export with complete user data isolation.
"""

import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, Response, abort, jsonify

from utils.expense_helpers import (
    get_categories,
    create_expense,
    get_expense_by_id,
    update_expense,
    delete_expense,
    get_expenses,
    get_expenses_summary
)
from utils.nlp_parser import parse_expense_sentence

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')


@expenses_bp.before_request
def require_login():
    """Ensure user is authenticated before accessing any expense endpoints."""
    if g.user is None:
        flash('Please log in to access your expenses.', 'error')
        return redirect(url_for('auth.login', next=request.path))


@expenses_bp.route('', strict_slashes=False)
@expenses_bp.route('/', strict_slashes=False)
def index():
    """Display expense table with dynamic filtering and summary KPIs."""
    category_id = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')

    user_id = g.user['id']
    categories = get_categories()
    expenses = get_expenses(
        user_id=user_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )
    summary = get_expenses_summary(
        user_id=user_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date
    )

    return render_template(
        'expenses/index.html',
        expenses=expenses,
        categories=categories,
        summary=summary,
        selected_category=category_id or '',
        start_date=start_date or '',
        end_date=end_date or '',
        sort_by=sort_by,
        sort_order=sort_order
    )


@expenses_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Record a new manual expense."""
    categories = get_categories()
    today = date.today().isoformat()

    if request.method == 'POST':
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        expense_date = request.form.get('expense_date') or today
        note = request.form.get('note', '')

        try:
            create_expense(
                user_id=g.user['id'],
                category_id=category_id,
                amount=amount,
                expense_date=expense_date,
                note=note
            )
            flash(f'Expense of ₹{float(amount):.2f} added successfully!', 'success')
            return redirect(url_for('expenses.index'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template(
                'expenses/form.html',
                action_title='Add New Expense',
                button_text='Save Expense',
                categories=categories,
                expense={
                    'amount': amount or '',
                    'category_id': int(category_id) if category_id and category_id.isdigit() else '',
                    'expense_date': expense_date,
                    'note': note or ''
                },
                is_edit=False
            )

    init_expense = {
        'expense_date': today,
        'amount': request.args.get('amount', ''),
        'category_id': int(request.args.get('category_id')) if request.args.get('category_id', '').isdigit() else '',
        'note': request.args.get('note', '')
    }

    return render_template(
        'expenses/form.html',
        action_title='Add New Expense',
        button_text='Save Expense',
        categories=categories,
        expense=init_expense,
        is_edit=False
    )


@expenses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit an existing expense owned by the current user."""
    user_id = g.user['id']
    expense = get_expense_by_id(id, user_id)

    if expense is None:
        flash('Expense not found or unauthorized access.', 'error')
        return redirect(url_for('expenses.index'))

    categories = get_categories()

    if request.method == 'POST':
        amount = request.form.get('amount')
        category_id = request.form.get('category_id')
        expense_date = request.form.get('expense_date')
        note = request.form.get('note', '')

        try:
            updated = update_expense(
                expense_id=id,
                user_id=user_id,
                category_id=category_id,
                amount=amount,
                expense_date=expense_date,
                note=note
            )
            if updated:
                flash('Expense updated successfully!', 'success')
                return redirect(url_for('expenses.index'))
            else:
                flash('Could not update expense. Record may have been removed.', 'error')
                return redirect(url_for('expenses.index'))
        except ValueError as e:
            flash(str(e), 'error')
            return render_template(
                'expenses/form.html',
                action_title='Edit Expense',
                button_text='Update Expense',
                categories=categories,
                expense={
                    'id': id,
                    'amount': amount or '',
                    'category_id': int(category_id) if category_id and category_id.isdigit() else '',
                    'expense_date': expense_date or expense['expense_date'],
                    'note': note or ''
                },
                is_edit=True
            )

    return render_template(
        'expenses/form.html',
        action_title='Edit Expense',
        button_text='Update Expense',
        categories=categories,
        expense=expense,
        is_edit=True
    )


@expenses_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete an expense record with strict ownership check."""
    user_id = g.user['id']
    deleted = delete_expense(id, user_id)

    if deleted:
        flash('Expense deleted successfully.', 'success')
    else:
        flash('Expense could not be found or you do not have permission to delete it.', 'error')

    return redirect(url_for('expenses.index'))


@expenses_bp.route('/export')
def export_csv():
    """Export filtered or complete expenses to an RFC 4180 CSV file."""
    category_id = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort', 'date')
    sort_order = request.args.get('order', 'desc')

    user_id = g.user['id']
    expenses = get_expenses(
        user_id=user_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Generate CSV stream
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header row
    writer.writerow(['Expense ID', 'Date', 'Category', 'Amount (INR)', 'Note', 'Logged At'])

    for exp in expenses:
        writer.writerow([
            exp['id'],
            exp['expense_date'],
            exp['category_name'],
            f"{exp['amount']:.2f}",
            exp['note'] or '',
            exp['created_at']
        ])

    filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Cache-Control': 'no-cache'
        }
    )


@expenses_bp.route('/ai-parse', methods=['POST'])
def ai_parse():
    """
    Parse a natural language expense sentence via AJAX/Fetch API.
    Returns JSON structure containing parsed amount, category, confidence, and date.
    Supports prefer_gemini option (defaults to True on Quick-add requests).
    """
    data = request.get_json(silent=True) or request.form
    sentence = data.get('sentence', '').strip()
    prefer_gemini = data.get('prefer_gemini', True)

    if not sentence:
        return jsonify({'success': False, 'error': 'Please provide an expense description.'}), 400

    parsed = parse_expense_sentence(sentence, prefer_gemini=prefer_gemini)
    return jsonify({
        'success': True,
        'parsed': parsed
    })


@expenses_bp.route('/ai-quick-add', methods=['POST'])
def ai_quick_add():
    """
    Process natural language sentence and immediately record expense if amount is present,
    or redirect to pre-filled add form if amount is missing or category was overridden.
    """
    sentence = request.form.get('sentence', '').strip()
    override_category_id = request.form.get('category_id')
    form_amount = request.form.get('amount')
    form_note = request.form.get('note')

    if not sentence:
        flash('Please enter a sentence to record an expense.', 'error')
        return redirect(url_for('expenses.index'))

    parsed = parse_expense_sentence(sentence, prefer_gemini=True)
    
    # Use explicitly submitted form values if available from Quick-add, else parser results
    amount = parsed['amount']
    if form_amount:
        try:
            amount = float(form_amount)
        except (ValueError, TypeError):
            pass

    category_id = int(override_category_id) if override_category_id and override_category_id.isdigit() else parsed['category_id']
    category_name = parsed['category_name']
    note = form_note.strip() if form_note else parsed['description']
    expense_date = request.form.get('expense_date') or parsed['expense_date']

    if amount is None or amount <= 0:
        flash(f"Could not automatically detect an amount in '{sentence}'. Please fill in the amount.", 'warning')
        return redirect(url_for('expenses.add', note=note, category_id=category_id))

    try:
        create_expense(
            user_id=g.user['id'],
            category_id=category_id,
            amount=amount,
            expense_date=expense_date,
            note=note
        )
        conf_pct = int(parsed['confidence'] * 100)
        source_label = "Gemini AI" if parsed.get('model_source') == 'gemini_ai' else "Offline NLP"
        flash(
            f"✨ AI Quick-Add: Recorded ₹{amount:.2f} for {category_name} ({conf_pct}% confidence via {source_label})!",
            'success'
        )
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('expenses.index'))

