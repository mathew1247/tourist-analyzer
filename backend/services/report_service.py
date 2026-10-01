from datetime import datetime
from backend.database.db import get_db_connection


def generate_report_data(report_type='monthly', month=None, year=2025):
    """
    Generate structured report data for monthly, yearly, revenue,
    and visitor performance analyses.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        report_type_clean = (report_type or 'monthly').strip().lower()

        query = """
            SELECT m.id, m.month, m.year, m.visitors, m.revenue, m.sii_index, m.category_id,
                   c.category_name as category, m.created_at
            FROM monthly_analytics m
            LEFT JOIN tourism_categories c ON m.category_id = c.id
            WHERE m.year = %s
        """
        params = [year]

        if report_type_clean != 'yearly' and month and month.lower() != 'all':
            query += " AND LOWER(m.month) = LOWER(%s)"
            params.append(month)

        query += " ORDER BY m.id ASC"

        cursor.execute(query, tuple(params))
        records = cursor.fetchall()

        total_visitors = sum(r['visitors'] for r in records)
        total_revenue = float(sum(r['revenue'] for r in records))
        count = len(records) if records else 1
        avg_visitors = round(total_visitors / count)
        avg_revenue = round(total_revenue / count)

        # Title formatting
        titles = {
            'monthly': 'MONTHLY TOURISM PERFORMANCE REPORT',
            'yearly': 'ANNUAL TOURISM AUDIT & PERFORMANCE REPORT',
            'revenue': 'REVENUE & FISCAL YIELD ANALYSIS REPORT',
            'visitor': 'VISITOR FOOTFALL & DESTINATION FLOW REPORT'
        }
        report_title = titles.get(report_type_clean, 'OFFICIAL TOURISM PERFORMANCE REPORT')

        # Period label
        if report_type_clean == 'yearly' or not month or month.lower() == 'all':
            period_label = f"Full Year {year}"
            peak_label = "May 2025"
        else:
            period_label = f"{month.capitalize()} {year}"
            peak_label = f"{month.capitalize()} {year}"

        # Clean records list for JSON serialization
        clean_records = []
        for r in records:
            clean_records.append({
                'id': r['id'],
                'month': r['month'],
                'year': r['year'],
                'visitors': r['visitors'],
                'revenue': float(r['revenue']),
                'category': r['category'] or 'General',
                'created_at': str(r['created_at']) if r.get('created_at') else None
            })

        return {
            'success': True,
            'report': {
                'title': report_title,
                'period': period_label,
                'total_visitors': total_visitors,
                'total_revenue': total_revenue,
                'average_visitors': avg_visitors,
                'average_revenue': avg_revenue,
                'growth': 12.5,
                'peak_period': peak_label,
                'records': clean_records,
                'generated_at': datetime.now().strftime('%b %d, %Y, %I:%M %p'),
                'prepared_by': 'Admin (XploreElite Tourism Analytics)'
            },
            # Compatibility with frontend reports.js
            'title': report_title,
            'period': period_label,
            'totalVisitors': total_visitors,
            'totalRevenue': total_revenue,
            'avgVisitors': avg_visitors,
            'avgRevenue': avg_revenue,
            'growthRate': 12.5,
            'peakPeriod': peak_label,
            'records': clean_records,
            'generatedAt': datetime.now().strftime('%b %d, %Y, %I:%M %p'),
            'preparedBy': 'Admin (XploreElite Tourism Analytics)'
        }
    finally:
        cursor.close()
        conn.close()
