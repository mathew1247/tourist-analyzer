from flask import Blueprint, request, jsonify
from backend.services.analytics_service import get_analytics_data
from backend.database.db import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """
    Return executive tourism statistics, monthly trends, recent data rows,
    peak/low metrics, and category revenue distribution.
    """
    year = request.args.get('year', 2025)
    try:
        year = int(year)
    except (ValueError, TypeError):
        year = 2025

    try:
        # Use analytics service for core calculations
        analytics = get_analytics_data(year=year)

        # Query recent 5 records for the dashboard table
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id, m.month, m.year, m.visitors, m.revenue, c.category_name as category
            FROM monthly_analytics m
            LEFT JOIN tourism_categories c ON m.category_id = c.id
            WHERE m.year = %s
            ORDER BY m.id ASC
            LIMIT 5
        """, (year,))
        recent_rows = cursor.fetchall()
        cursor.close()
        conn.close()

        recent_records = []
        for r in recent_rows:
            recent_records.append({
                'id': r['id'],
                'month': r['month'],
                'year': r['year'],
                'visitors': r['visitors'],
                'revenue': float(r['revenue']),
                'category': r['category'] or 'General'
            })

        response_data = {
            'success': True,
            'summary': analytics['summary'],
            'monthly_visitors': analytics['visitor_trend'],
            'monthly_revenue': analytics['revenue_trend'],
            'recent_records': recent_records,
            'peak_month': analytics['peak_period'],
            'lowest_month': analytics['lowest_period'],
            # Frontend compatibility keys
            'metrics': analytics['metrics'],
            'charts': analytics['charts'],
            'recentRecords': recent_records,
            'categories': analytics['categories'],
            'destinations': analytics['destinations'],
            'quickStats': analytics['quickStats']
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f"Dashboard error: {str(e)}"}), 500
