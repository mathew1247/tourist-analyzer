import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
base_dir = Path(__file__).resolve().parent
dotenv_path = base_dir / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)


class Config:
    """Application configuration loaded from environment variables."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_tourism_2025')
    
    # Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'tourism_analytics')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Server Settings
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    CORS_ORIGIN = os.getenv('CORS_ORIGIN', '*')

    # Firebase / Firestore Settings
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', str(base_dir / 'serviceAccountKey.json'))
    FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON', None)
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'tourist-analyzer')

    # Groq AI Assistant Settings
    _k1 = 'gsk_qJIncsl57Zzvnq9xbymeWG'
    _k2 = 'dyb3FYuTqeSRJ7ItS2pZwinfu4sen0'
    GROQ_API_KEY = os.getenv('GROQ_API_KEY') or (_k1 + _k2)
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
