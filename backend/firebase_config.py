import os
import json
import base64
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from backend.config import Config

_firestore_client = None
_firebase_app = None


def get_firestore_client():
    """
    Initializes and returns the Google Cloud Firestore client via Firebase Admin SDK.
    Supports credentials from:
    1. FIREBASE_CREDENTIALS_JSON environment variable (raw JSON string or base64 encoded)
    2. FIREBASE_CREDENTIALS_PATH environment variable (relative or absolute file path)
    3. Default location: backend/serviceAccountKey.json or serviceAccountKey.json
    """
    global _firestore_client, _firebase_app

    if _firestore_client is not None:
        return _firestore_client

    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        cred = None

        # 1. Check for credentials directly in environment variable (Render / Cloud deployment)
        raw_json = os.getenv('FIREBASE_CREDENTIALS_JSON') or getattr(Config, 'FIREBASE_CREDENTIALS_JSON', None)
        if raw_json:
            try:
                cert_dict = json.loads(raw_json)
                cred = credentials.Certificate(cert_dict)
            except Exception:
                try:
                    decoded = base64.b64decode(raw_json).decode('utf-8')
                    cert_dict = json.loads(decoded)
                    cred = credentials.Certificate(cert_dict)
                except Exception as b64_err:
                    raise ValueError(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {b64_err}")

        # 2. Check for serviceAccountKey.json file path
        if not cred:
            candidate_paths = []
            
            cfg_path = os.getenv('FIREBASE_CREDENTIALS_PATH') or getattr(Config, 'FIREBASE_CREDENTIALS_PATH', None)
            if cfg_path:
                candidate_paths.append(Path(cfg_path))
                candidate_paths.append(Path(__file__).resolve().parent / cfg_path)
                candidate_paths.append(Path(__file__).resolve().parent.parent / cfg_path)

            backend_dir = Path(__file__).resolve().parent
            candidate_paths.extend([
                backend_dir / 'serviceAccountKey.json',
                backend_dir.parent / 'serviceAccountKey.json'
            ])

            resolved_path = None
            for p in candidate_paths:
                if p.is_file():
                    resolved_path = p.resolve()
                    break

            if resolved_path:
                cred = credentials.Certificate(str(resolved_path))
            else:
                raise FileNotFoundError(
                    "Firebase service account key file not found. "
                    "Ensure 'serviceAccountKey.json' exists in backend/ or set FIREBASE_CREDENTIALS_PATH / FIREBASE_CREDENTIALS_JSON."
                )

        _firebase_app = firebase_admin.initialize_app(cred, {
            'projectId': getattr(Config, 'FIREBASE_PROJECT_ID', 'tourist-analyzer')
        })

    _firestore_client = firestore.client()
    return _firestore_client


# Module-level client accessor
class _LazyFirestoreProxy:
    """Proxy to allow accessing `db.collection(...)` with lazy initialization."""
    def __getattr__(self, name):
        client = get_firestore_client()
        return getattr(client, name)


db = _LazyFirestoreProxy()
