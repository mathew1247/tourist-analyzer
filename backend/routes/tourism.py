from flask import Blueprint, request, jsonify
from backend.database.db import get_db_connection
from backend.utils.validators import validate_tourism_payload

tourism_bp = Blueprint('tourism', __name__)


def resolve_category_id(cursor, category_id=None, category_name=None):
    """Resolve category_id from integer id or category_name string."""
    if category_id:
        cursor.execute("SELECT id FROM tourism_categories WHERE id = %s", (category_id,))
        cat = cursor.fetchone()
        if cat:
            return cat['id']
    if category_name:
        cursor.execute("SELECT id FROM tourism_categories WHERE LOWER(category_name) = LOWER(%s)", (category_name.strip(),))
        cat = cursor.fetchone()
        if cat:
            return cat['id']
        # If new category name provided, insert it
        cursor.execute("INSERT INTO tourism_categories (category_name) VALUES (%s)", (category_name.strip(),))
        return cursor.lastrowid
    return None


@tourism_bp.route('/api/tourism', methods=['POST'])
def create_tourism_record():
    """Create a new monthly tourism analytics record."""
    data = request.get_json(silent=True) or {}
    is_valid, err_msg, cleaned = validate_tourism_payload(data, is_update=False)

    if not is_valid:
        return jsonify({'success': False, 'message': err_msg}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cat_id = resolve_category_id(
            cursor,
            category_id=cleaned.get('category_id'),
            category_name=cleaned.get('category_name')
        )

        cursor.execute("""
            INSERT INTO monthly_analytics (month, year, visitors, revenue, sii_index, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            cleaned['month'],
            cleaned['year'],
            cleaned['visitors'],
            cleaned['revenue'],
            cleaned.get('sii_index'),
            cat_id
        ))
        conn.commit()
        new_id = cursor.lastrowid

        return jsonify({
            'success': True,
            'message': 'Tourism data added successfully',
            'data': {'id': new_id}
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@tourism_bp.route('/api/tourism', methods=['GET'])
def get_tourism_records():
    """Return filtered historical tourism records."""
    year = request.args.get('year')
    month = request.args.get('month')
    search = request.args.get('search')
    category = request.args.get('category')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT m.id, m.month, m.year, m.visitors, m.revenue, m.sii_index, m.category_id,
                   c.category_name as category, m.created_at, m.updated_at
            FROM monthly_analytics m
            LEFT JOIN tourism_categories c ON m.category_id = c.id
            WHERE 1=1
        """
        params = []

        if year and year.lower() != 'all':
            query += " AND m.year = %s"
            params.append(int(year))

        if month and month.lower() != 'all':
            query += " AND LOWER(m.month) = LOWER(%s)"
            params.append(month.strip())

        if category and category.lower() != 'all':
            query += " AND LOWER(c.category_name) = LOWER(%s)"
            params.append(category.strip())

        if search:
            query += " AND (LOWER(m.month) LIKE %s OR CAST(m.year AS CHAR) LIKE %s OR LOWER(c.category_name) LIKE %s)"
            pattern = f"%{search.strip().lower()}%"
            params.extend([pattern, pattern, pattern])

        query += " ORDER BY m.year DESC, m.id DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        # Format rows for JSON serialization
        results = []
        for r in rows:
            results.append({
                'id': r['id'],
                'month': r['month'],
                'year': r['year'],
                'visitors': r['visitors'],
                'revenue': float(r['revenue']),
                'category': r['category'] or 'General',
                'category_id': r['category_id'],
                'sii_index': r['sii_index'],
                'created_at': str(r['created_at']) if r.get('created_at') else None
            })

        return jsonify({
            'success': True,
            'data': results
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@tourism_bp.route('/api/tourism/<int:record_id>', methods=['GET'])
def get_tourism_record(record_id):
    """Return a single tourism record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT m.id, m.month, m.year, m.visitors, m.revenue, m.sii_index, m.category_id,
                   c.category_name as category, m.created_at, m.updated_at
            FROM monthly_analytics m
            LEFT JOIN tourism_categories c ON m.category_id = c.id
            WHERE m.id = %s
        """, (record_id,))
        r = cursor.fetchone()

        if not r:
            return jsonify({'success': False, 'message': 'Tourism record not found'}), 404

        record = {
            'id': r['id'],
            'month': r['month'],
            'year': r['year'],
            'visitors': r['visitors'],
            'revenue': float(r['revenue']),
            'category': r['category'] or 'General',
            'category_id': r['category_id'],
            'sii_index': r['sii_index'],
            'created_at': str(r['created_at']) if r.get('created_at') else None
        }

        return jsonify({'success': True, 'data': record}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@tourism_bp.route('/api/tourism/<int:record_id>', methods=['PUT'])
def update_tourism_record(record_id):
    """Update an existing tourism record."""
    data = request.get_json(silent=True) or {}
    is_valid, err_msg, cleaned = validate_tourism_payload(data, is_update=True)

    if not is_valid:
        return jsonify({'success': False, 'message': err_msg}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if record exists
        cursor.execute("SELECT * FROM monthly_analytics WHERE id = %s", (record_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({'success': False, 'message': 'Tourism record not found'}), 404

        cat_id = existing['category_id']
        if 'category_id' in cleaned or 'category_name' in cleaned:
            cat_id = resolve_category_id(
                cursor,
                category_id=cleaned.get('category_id'),
                category_name=cleaned.get('category_name')
            )

        new_month = cleaned.get('month', existing['month'])
        new_year = cleaned.get('year', existing['year'])
        new_visitors = cleaned.get('visitors', existing['visitors'])
        new_revenue = cleaned.get('revenue', existing['revenue'])
        new_sii = cleaned.get('sii_index', existing['sii_index'])

        cursor.execute("""
            UPDATE monthly_analytics
            SET month = %s, year = %s, visitors = %s, revenue = %s, sii_index = %s, category_id = %s
            WHERE id = %s
        """, (new_month, new_year, new_visitors, new_revenue, new_sii, cat_id, record_id))
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Tourism record updated successfully',
            'data': {
                'id': record_id,
                'month': new_month,
                'year': new_year,
                'visitors': new_visitors,
                'revenue': float(new_revenue),
                'category_id': cat_id
            }
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@tourism_bp.route('/api/tourism/<int:record_id>', methods=['DELETE'])
def delete_tourism_record(record_id):
    """Delete a tourism record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id FROM monthly_analytics WHERE id = %s", (record_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Tourism record not found'}), 404

        cursor.execute("DELETE FROM monthly_analytics WHERE id = %s", (record_id,))
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Tourism record deleted successfully'
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
