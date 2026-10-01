import logging
from flask import Blueprint, request, jsonify
from backend.firebase_config import get_firestore_client
from backend.utils.validators import validate_tourist_firestore_payload

logger = logging.getLogger(__name__)

tourists_bp = Blueprint('tourists', __name__)

COLLECTION_NAME = 'tourist_data'


@tourists_bp.route('/api/tourists', methods=['GET'])
def get_all_tourists():
    """
    Retrieve all tourist records from Firestore 'tourist_data' collection.
    Returns:
        JSON list of tourist records with Firestore document ID as 'id'.
    """
    try:
        db = get_firestore_client()
    except Exception as e:
        logger.error(f"Firestore initialization error: {e}")
        return jsonify({
            'success': False,
            'message': 'Firestore service is currently unavailable. Please verify Firebase credentials.'
        }), 503

    try:
        collection_ref = db.collection(COLLECTION_NAME)
        docs = collection_ref.stream()

        records = []
        for doc in docs:
            doc_data = doc.to_dict() or {}
            record = {
                'id': doc.id,
                'location': doc_data.get('location', ''),
                'district': doc_data.get('district', ''),
                'state': doc_data.get('state', ''),
                'visit_date': doc_data.get('visit_date', ''),
                'visitor_count': doc_data.get('visitor_count', 0),
                'visitor_type': doc_data.get('visitor_type', 'Domestic'),
                'revenue': doc_data.get('revenue', 0)
            }
            records.append(record)

        # Return JSON array as specified in the schema
        return jsonify(records), 200

    except Exception as e:
        logger.error(f"Firestore query error: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving records from Firestore.'
        }), 500


@tourists_bp.route('/api/tourists', methods=['POST'])
def add_tourist_record():
    """
    Insert a new tourist record into Firestore 'tourist_data' collection.
    Accepts JSON body:
        location: str (required)
        district: str
        state: str
        visit_date: str (required)
        visitor_count: int >= 0 (required)
        visitor_type: str (default: 'Domestic')
        revenue: float/int >= 0 (required)
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'message': 'Invalid JSON format or missing Content-Type: application/json header'
        }), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            'success': False,
            'message': 'Invalid JSON body.'
        }), 400

    is_valid, error_msg, cleaned = validate_tourist_firestore_payload(data)
    if not is_valid:
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400

    try:
        db = get_firestore_client()
    except Exception as e:
        logger.error(f"Firestore initialization error: {e}")
        return jsonify({
            'success': False,
            'message': 'Firestore service is currently unavailable. Please verify Firebase credentials.'
        }), 503

    try:
        # Write to Firestore collection
        update_time, doc_ref = db.collection(COLLECTION_NAME).add(cleaned)

        response_data = {
            'id': doc_ref.id,
            **cleaned
        }

        return jsonify({
            'success': True,
            'message': 'Tourist record added successfully',
            'id': doc_ref.id,
            'data': response_data
        }), 201

    except Exception as e:
        logger.error(f"Firestore insert error: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to save tourist record to Firestore.'
        }), 500


@tourists_bp.route('/api/tourists/<doc_id>', methods=['GET'])
def get_tourist_by_id(doc_id):
    """Retrieve a single tourist record from Firestore by document ID."""
    try:
        db = get_firestore_client()
        doc = db.collection(COLLECTION_NAME).document(doc_id).get()
        if not doc.exists:
            return jsonify({'success': False, 'message': 'Tourist record not found'}), 404

        data = doc.to_dict() or {}
        return jsonify({
            'id': doc.id,
            'location': data.get('location', ''),
            'district': data.get('district', ''),
            'state': data.get('state', ''),
            'visit_date': data.get('visit_date', ''),
            'visitor_count': data.get('visitor_count', 0),
            'visitor_type': data.get('visitor_type', 'Domestic'),
            'revenue': data.get('revenue', 0)
        }), 200
    except Exception as e:
        logger.error(f"Firestore get error: {e}")
        return jsonify({'success': False, 'message': 'Error retrieving record from Firestore'}), 500


@tourists_bp.route('/api/tourists/<doc_id>', methods=['DELETE'])
def delete_tourist_by_id(doc_id):
    """Delete a single tourist record from Firestore by document ID."""
    try:
        db = get_firestore_client()
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        if not doc_ref.get().exists:
            return jsonify({'success': False, 'message': 'Tourist record not found'}), 404

        doc_ref.delete()
        return jsonify({
            'success': True,
            'message': 'Tourist record deleted successfully',
            'id': doc_id
        }), 200
    except Exception as e:
        logger.error(f"Firestore delete error: {e}")
        return jsonify({'success': False, 'message': 'Error deleting record from Firestore'}), 500
