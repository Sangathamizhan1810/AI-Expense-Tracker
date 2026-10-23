"""
Expense helpers module: database operations, filtering, and validation
strictly isolated by user_id.
"""

from datetime import datetime, date
from utils.db import get_db


def get_categories():
    """Fetch all expense categories sorted alphabetically."""
    db = get_db()
    cursor = db.execute("SELECT id, name FROM categories ORDER BY name ASC")
    return cursor.fetchall()


def get_category_by_id(category_id):
    """Fetch a category by ID."""
    db = get_db()
    cursor = db.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,))
    return cursor.fetchone()


def validate_expense_data(amount, category_id, expense_date, note=None):
    """
    Validate expense input parameters.
    Returns cleaned tuple: (float_amount, int_category_id, str_date, str_note).
    Raises ValueError with descriptive message if validation fails.
    """
    # 1. Amount validation
    try:
        float_amount = round(float(amount), 2)
        if float_amount <= 0:
            raise ValueError("Amount must be greater than 0.")
    except (ValueError, TypeError):
        raise ValueError("Please enter a valid numeric amount greater than 0.")

    # 2. Category validation
    try:
        int_category_id = int(category_id)
    except (ValueError, TypeError):
        raise ValueError("Please select a valid expense category.")

    cat = get_category_by_id(int_category_id)
    if cat is None:
        raise ValueError("Selected category does not exist.")

    # 3. Date validation
    if not expense_date:
        str_date = date.today().isoformat()
    else:
        try:
            # Verify format YYYY-MM-DD
            parsed_date = datetime.strptime(str(expense_date).strip(), "%Y-%m-%d")
            str_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")

    # 4. Note validation (optional, max 255 chars)
    str_note = (note or "").strip()
    if len(str_note) > 255:
        str_note = str_note[:255]

    return float_amount, int_category_id, str_date, str_note


def create_expense(user_id, category_id, amount, expense_date, note=None):
    """
    Validate and insert a new expense record for the given user.
    Returns the newly created expense ID.
    """
    float_amount, int_category_id, str_date, str_note = validate_expense_data(
        amount, category_id, expense_date, note
    )

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO expenses (user_id, category_id, amount, expense_date, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, int_category_id, float_amount, str_date, str_note)
    )
    db.commit()
    return cursor.lastrowid


def get_expense_by_id(expense_id, user_id):
    """
    Fetch a single expense by ID, strictly enforcing user_id ownership.
    Returns sqlite3.Row or None if not found or unauthorized.
    """
    db = get_db()
    cursor = db.execute(
        """
        SELECT e.id, e.user_id, e.category_id, e.amount, e.expense_date, e.note, e.created_at,
               c.name AS category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ? AND e.user_id = ?
        """,
        (expense_id, user_id)
    )
    return cursor.fetchone()


def update_expense(expense_id, user_id, category_id, amount, expense_date, note=None):
    """
    Validate inputs and update an existing expense record for the user.
    Returns True if successfully updated, False if expense not found or unauthorized.
    """
    # Verify existence and ownership first
    existing = get_expense_by_id(expense_id, user_id)
    if existing is None:
        return False

    float_amount, int_category_id, str_date, str_note = validate_expense_data(
        amount, category_id, expense_date, note
    )

    db = get_db()
    cursor = db.execute(
        """
        UPDATE expenses
        SET category_id = ?, amount = ?, expense_date = ?, note = ?
        WHERE id = ? AND user_id = ?
        """,
        (int_category_id, float_amount, str_date, str_note, expense_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def delete_expense(expense_id, user_id):
    """
    Delete an expense record strictly matching both id and user_id.
    Returns True if deleted, False if not found or unauthorized.
    """
    db = get_db()
    cursor = db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def get_expenses(user_id, category_id=None, start_date=None, end_date=None,
                 sort_by='date', sort_order='desc', limit=None, offset=None):
    """
    Query expenses for a user with dynamic filtering, sorting whitelist, and pagination.
    """
    db = get_db()
    params = [user_id]
    query = [
        """
        SELECT e.id, e.user_id, e.category_id, e.amount, e.expense_date, e.note, e.created_at,
               c.name AS category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        """
    ]

    # Category filter
    if category_id:
        try:
            cid = int(category_id)
            query.append("AND e.category_id = ?")
            params.append(cid)
        except (ValueError, TypeError):
            pass

    # Date range filters
    if start_date:
        query.append("AND e.expense_date >= ?")
        params.append(str(start_date).strip())

    if end_date:
        query.append("AND e.expense_date <= ?")
        params.append(str(end_date).strip())

    # Sorting whitelist
    sort_column_map = {
        'date': 'e.expense_date',
        'amount': 'e.amount',
        'created_at': 'e.created_at'
    }
    col = sort_column_map.get(sort_by, 'e.expense_date')
    order = 'ASC' if str(sort_order).lower() == 'asc' else 'DESC'

    query.append(f"ORDER BY {col} {order}, e.id DESC")

    # Pagination
    if limit is not None:
        query.append("LIMIT ?")
        params.append(int(limit))
        if offset is not None:
            query.append("OFFSET ?")
            params.append(int(offset))

    sql = " ".join(query)
    cursor = db.execute(sql, params)
    return cursor.fetchall()


def get_expenses_summary(user_id, category_id=None, start_date=None, end_date=None):
    """
    Calculate summary aggregate metrics (count and total sum in INR)
    for filtered expenses of a user.
    """
    db = get_db()
    params = [user_id]
    query = [
        """
        SELECT COUNT(*) AS total_count, COALESCE(SUM(amount), 0.0) AS total_amount
        FROM expenses
        WHERE user_id = ?
        """
    ]

    if category_id:
        try:
            cid = int(category_id)
            query.append("AND category_id = ?")
            params.append(cid)
        except (ValueError, TypeError):
            pass

    if start_date:
        query.append("AND expense_date >= ?")
        params.append(str(start_date).strip())

    if end_date:
        query.append("AND expense_date <= ?")
        params.append(str(end_date).strip())

    sql = " ".join(query)
    cursor = db.execute(sql, params)
    row = cursor.fetchone()
    return {
        'total_count': row['total_count'] if row else 0,
        'total_amount': round(row['total_amount'], 2) if row else 0.0
    }
