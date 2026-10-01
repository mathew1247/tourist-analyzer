from flask import Blueprint, request, jsonify
from backend.services.report_service import generate_report_data

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/reports', methods=['GET'])
def get_reports():
    """
    Generate and return structured report summaries for executive auditing,
    breakdowns, and printing.
    """
    report_type = request.args.get('type', 'monthly')
    month = request.args.get('month', 'January')
    year = request.args.get('year', 2025)

    try:
        year = int(year)
    except (ValueError, TypeError):
        year = 2025

    try:
        data = generate_report_data(report_type=report_type, month=month, year=year)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f"Report generation error: {str(e)}"}), 500
