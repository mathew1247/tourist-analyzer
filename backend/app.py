import os
import sys
from pathlib import Path

# Add project root to sys.path so backend can be imported regardless of working directory
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, jsonify, send_from_directory, redirect
from flask_cors import CORS

from backend.config import Config
from backend.database.db import init_db

# Import Route Blueprints
from backend.routes.auth import auth_bp
from backend.routes.tourism import tourism_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.analytics import analytics_bp
from backend.routes.prediction import prediction_bp
from backend.routes.reports import reports_bp
from backend.routes.profile import profile_bp
from backend.routes.tourists import tourists_bp

# Define Paths for static and templates
ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_FOLDER = str(ROOT_DIR / 'static')
TEMPLATES_FOLDER = str(ROOT_DIR / 'templates')


def create_app():
    """Application factory for Tourism Analytics Platform."""
    app = Flask(
        __name__,
        static_folder=STATIC_FOLDER,
        static_url_path='/static'
    )
    
    # Configure App
    app.config.from_object(Config)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGIN}}, supports_credentials=True)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(tourism_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(tourists_bp)


    # ----------------------------------------------------------------------
    # System & Health Check Endpoints
    # ----------------------------------------------------------------------
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'success': True,
            'message': 'Tourism Analytics API is running'
        }), 200

    # ----------------------------------------------------------------------
    # Optional Frontend Serving Routes (For unified single-port local hosting)
    # ----------------------------------------------------------------------
    @app.route('/')
    def root_index():
        return redirect('/templates/login.html')

    @app.route('/templates/<path:filename>')
    def serve_template_page(filename):
        return send_from_directory(TEMPLATES_FOLDER, filename)

    @app.route('/<string:page>.html')
    def serve_root_html(page):
        return send_from_directory(TEMPLATES_FOLDER, f"{page}.html")

    # ----------------------------------------------------------------------
    # Global JSON Error Handlers (Ensures APIs never return HTML errors)
    # ----------------------------------------------------------------------
    @app.errorhandler(400)
    def bad_request_error(e):
        return jsonify({'success': False, 'message': 'Bad Request: ' + str(e.description)}), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401

    @app.errorhandler(404)
    def not_found_error(e):
        return jsonify({'success': False, 'message': 'Endpoint or resource not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed_error(e):
        return jsonify({'success': False, 'message': 'HTTP Method not allowed'}), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    return app


# Create and initialize
app = create_app()

if __name__ == '__main__':
    # Initialize database tables and seed sample data
    try:
        init_db()
    except Exception as ex:
        print(f"[Warning] DB initialization: {ex}")

    print(f"\n=======================================================")
    print(f" Tourism Footfall & Revenue Analytics API Server")
    print(f" Serving on: http://127.0.0.1:{Config.PORT}")
    print(f" Health check: http://127.0.0.1:{Config.PORT}/api/health")
    print(f"=======================================================\n")

    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
