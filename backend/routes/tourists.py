import logging
from flask import Blueprint, request, jsonify
from backend.database.db import get_db_connection

logger = logging.getLogger(__name__)

tourists_bp = Blueprint('tourists', __name__)

COLLECTION_NAME = 'tourist_data'


def _get_firestore():
    try:
        from backend.firebase_config import get_firestore_client
        return get_firestore_client()
    except Exception as e:
        logger.debug(f"Firestore not available: {e}")
        return None


@tourists_bp.route('/api/tourists', methods=['GET'])
def get_all_tourists():
    """
    Retrieve all tourist records.
    Prioritizes Firestore 'tourist_data' collection; falls back gracefully to SQL 'tourist_entries'.
    """
    db = _get_firestore()
    if db is not None:
        try:
            collection_ref = db.collection(COLLECTION_NAME)
            docs = collection_ref.stream()
            records = []
            for doc in docs:
                doc_data = doc.to_dict() or {}
                record = {
                    'id': doc.id,
                    'fullName': doc_data.get('full_name') or doc_data.get('fullName', ''),
                    'age': doc_data.get('age', ''),
                    'gender': doc_data.get('gender', ''),
                    'country': doc_data.get('country', ''),
                    'touristPlace': doc_data.get('tourist_place') or doc_data.get('location', ''),
                    'location': doc_data.get('tourist_place') or doc_data.get('location', ''),
                    'visitDate': doc_data.get('visit_date') or doc_data.get('date', ''),
                    'visitTime': doc_data.get('visit_time') or doc_data.get('time', ''),
                    'ticketPrice': doc_data.get('ticket_price', 0),
                    'additionalSpending': doc_data.get('additional_spending', 0),
                    'groupType': doc_data.get('group_type', 'Individual'),
                    'numberOfVisitors': doc_data.get('number_of_visitors') or doc_data.get('visitor_count', 1),
                    'visitor_count': doc_data.get('number_of_visitors') or doc_data.get('visitor_count', 1),
                    'feedback': doc_data.get('feedback', ''),
                    'totalRevenue': doc_data.get('total_revenue') or doc_data.get('revenue', 0),
                    'revenue': doc_data.get('total_revenue') or doc_data.get('revenue', 0)
                }
                records.append(record)
            return jsonify(records), 200
        except Exception as e:
            logger.error(f"Firestore query error: {e}")

    # Fallback to local SQL database
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tourist_entries ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        records = []
        for r in rows:
            records.append({
                'id': r['id'],
                'fullName': r.get('full_name', ''),
                'age': r.get('age', ''),
                'gender': r.get('gender', ''),
                'country': r.get('country', ''),
                'touristPlace': r.get('tourist_place', ''),
                'location': r.get('tourist_place', ''),
                'visitDate': r.get('visit_date', ''),
                'visitTime': r.get('visit_time', ''),
                'ticketPrice': float(r.get('ticket_price') or 0),
                'additionalSpending': float(r.get('additional_spending') or 0),
                'groupType': r.get('group_type', 'Individual'),
                'numberOfVisitors': int(r.get('number_of_visitors') or 1),
                'visitor_count': int(r.get('number_of_visitors') or 1),
                'feedback': r.get('feedback', ''),
                'totalRevenue': float(r.get('total_revenue') or 0),
                'revenue': float(r.get('total_revenue') or 0)
            })
        return jsonify(records), 200
    except Exception as sql_err:
        logger.error(f"Database query error: {sql_err}")
        return jsonify([]), 200


@tourists_bp.route('/api/tourists', methods=['POST'])
def add_tourist_record():
    """
    Insert a new tourist record (Fig. 2 Input Design).
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'Invalid JSON format or missing Content-Type: application/json header'
        }), 400

    data = request.get_json(silent=True) or {}

    full_name = str(data.get('fullName') or data.get('full_name') or data.get('name') or '').strip()
    tourist_place = str(data.get('touristPlace') or data.get('tourist_place') or data.get('location') or '').strip()

    if not tourist_place:
        return jsonify({'success': False, 'message': 'Tourist place / location is required.'}), 400

    age = int(data.get('age')) if data.get('age') not in (None, '') else None
    gender = str(data.get('gender') or '').strip()
    country = str(data.get('country') or 'India').strip()
    visit_date = str(data.get('visitDate') or data.get('visit_date') or data.get('date') or '').strip()
    visit_time = str(data.get('visitTime') or data.get('visit_time') or data.get('time') or '10:00').strip()
    ticket_price = float(data.get('ticketPrice') or data.get('ticket_price') or 0)
    additional_spending = float(data.get('additionalSpending') or data.get('additional_spending') or 0)
    group_type = str(data.get('groupType') or data.get('group_type') or 'Individual').strip()
    visitors = int(data.get('numberOfVisitors') or data.get('visitor_count') or data.get('visitors') or 1)
    feedback = str(data.get('feedback') or '').strip()

    total_revenue = float(data.get('totalRevenue') or data.get('revenue') or ((ticket_price * visitors) + additional_spending))

    cleaned = {
        'full_name': full_name,
        'age': age,
        'gender': gender,
        'country': country,
        'tourist_place': tourist_place,
        'location': tourist_place,
        'visit_date': visit_date,
        'visit_time': visit_time,
        'ticket_price': ticket_price,
        'additional_spending': additional_spending,
        'group_type': group_type,
        'number_of_visitors': visitors,
        'visitor_count': visitors,
        'feedback': feedback,
        'total_revenue': total_revenue,
        'revenue': total_revenue
    }

    # Try Firestore first if available
    db = _get_firestore()
    if db is not None:
        try:
            update_time, doc_ref = db.collection(COLLECTION_NAME).add(cleaned)
            return jsonify({
                'success': True,
                'message': 'Tourist record added successfully',
                'id': doc_ref.id,
                'data': {'id': doc_ref.id, **cleaned}
            }), 201
        except Exception as e:
            logger.error(f"Firestore insert error: {e}")

    # Fallback to local SQL database
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO tourist_entries (
                full_name, age, gender, country, tourist_place,
                visit_date, visit_time, ticket_price, additional_spending,
                group_type, number_of_visitors, feedback, total_revenue
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            full_name, age, gender, country, tourist_place,
            visit_date, visit_time, ticket_price, additional_spending,
            group_type, visitors, feedback, total_revenue
        ))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Tourist record added successfully',
            'id': new_id,
            'data': {'id': new_id, **cleaned}
        }), 201
    except Exception as sql_err:
        logger.error(f"Database insert error: {sql_err}")
        return jsonify({'success': False, 'message': f"Database error: {str(sql_err)}"}), 500


@tourists_bp.route('/api/tourists/<doc_id>', methods=['DELETE'])
def delete_tourist_by_id(doc_id):
    """Delete a single tourist record."""
    db = _get_firestore()
    if db is not None:
        try:
            doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
            if doc_ref.get().exists:
                doc_ref.delete()
                return jsonify({'success': True, 'message': 'Tourist record deleted successfully', 'id': doc_id}), 200
        except Exception as e:
            logger.error(f"Firestore delete error: {e}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("DELETE FROM tourist_entries WHERE id = %s", (doc_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Tourist record deleted successfully', 'id': doc_id}), 200
    except Exception as sql_err:
        return jsonify({'success': False, 'message': str(sql_err)}), 500
