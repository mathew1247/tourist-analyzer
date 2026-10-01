from flask import Blueprint, request, jsonify
from backend.services.analytics_service import get_analytics_data

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Return deep analytical breakdown including trends, YoY growth rates,
    peak/low metrics, and factual observations.
    """
    year = request.args.get('year', 2025)
    month = request.args.get('month')
    category_id = request.args.get('category_id') or request.args.get('category')

    try:
        year = int(year)
    except (ValueError, TypeError):
        year = 2025

    try:
        data = get_analytics_data(year=year, month=month, category_id=category_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f"Analytics error: {str(e)}"}), 500
