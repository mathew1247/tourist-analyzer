from flask import Blueprint, request, jsonify
from backend.services.prediction_service import get_prediction_data

prediction_bp = Blueprint('prediction', __name__)


@prediction_bp.route('/api/prediction', methods=['GET'])
def get_prediction():
    """
    Return simple trend-based predictions using moving averages
    and historical growth rates.
    """
    period = request.args.get('period', '1')

    try:
        data = get_prediction_data(period=period)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f"Prediction error: {str(e)}"}), 500
