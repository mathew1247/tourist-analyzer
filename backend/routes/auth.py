from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.db import get_db_connection
from backend.utils.validators import validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Authenticate user credentials strictly against real database records."""
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Email/Username and password are required.'
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Search by email or username (case-insensitive)
        cursor.execute("""
            SELECT * FROM users 
            WHERE LOWER(email) = LOWER(%s) OR LOWER(username) = LOWER(%s) 
            LIMIT 1
        """, (email, email))
        user = cursor.fetchone()

        if not user or not check_password_hash(user['password'], password):
            return jsonify({
                'success': False,
                'message': 'Invalid email/username or password. Please check your credentials.'
            }), 401

        # Update last login timestamp
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))

        # Log to user_logs audit table
        cursor.execute(
            "INSERT INTO user_logs (user_id, username, access_level) VALUES (%s, %s, %s)",
            (user['id'], user['username'], user.get('role', 'admin'))
        )
        conn.commit()

        # Save session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_role'] = user.get('role', 'admin')
        session['user_username'] = user['username']

        user_payload = {
            'id': user['id'],
            'username': user['username'],
            'fullName': user['username'],
            'email': user['email'],
            'role': user.get('role', 'admin'),
            'phone': user.get('phone') or '+91 98765 43210',
            'companyName': user.get('company_name') or 'XploreElite Tourism Analytics Ltd.'
        }

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_payload,
            'data': user_payload
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f"Database error during login: {str(e)}"
        }), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/api/register', methods=['POST'])
def register():
    """Register a new user account and store credentials securely in the database."""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or data.get('fullName') or '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    phone = data.get('phone', '+91 98765 43210').strip()
    company_name = data.get('companyName', 'XploreElite Tourism Analytics Ltd.').strip()

    if not username or not email or not password:
        return jsonify({
            'success': False,
            'message': 'Full name, email address, and password are required.'
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'Password must be at least 6 characters long.'
        }), 400

    valid, err_or_clean = validate_email(email)
    if not valid:
        return jsonify({'success': False, 'message': err_or_clean}), 400
    email = err_or_clean

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if email is already registered
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'An account with this email address already exists. Please sign in instead.'
            }), 409

        hashed_pwd = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, email, password, role, phone, company_name)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, email, hashed_pwd, 'Admin', phone, company_name))
        conn.commit()

        new_user_id = cursor.lastrowid

        # Update session
        session['user_id'] = new_user_id
        session['user_email'] = email
        session['user_role'] = 'Admin'
        session['user_username'] = username

        user_payload = {
            'id': new_user_id,
            'username': username,
            'fullName': username,
            'email': email,
            'role': 'Administrator',
            'phone': phone,
            'companyName': company_name
        }

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user_payload,
            'data': user_payload
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f"Database error during registration: {str(e)}"
        }), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route('/api/logout', methods=['POST', 'GET'])
def logout():
    """Clear session data."""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200
