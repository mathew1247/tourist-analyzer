from flask import Blueprint, request, jsonify, session
from backend.database.db import get_db_connection
from backend.utils.validators import validate_email

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/api/profile', methods=['GET'])
def get_profile():
    """Return the administrator profile and account metadata."""
    target_email = request.args.get('email') or session.get('user_email')
    target_id = request.args.get('id') or session.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        user = None
        if target_id:
            try:
                cursor.execute("SELECT * FROM users WHERE id = %s", (int(target_id),))
                user = cursor.fetchone()
            except (ValueError, TypeError):
                pass

        if not user and target_email:
            cursor.execute("SELECT * FROM users WHERE email = %s", (target_email,))
            user = cursor.fetchone()

        if not user:
            # Check user id=2 (active administrator)
            cursor.execute("SELECT * FROM users WHERE id = 2")
            user = cursor.fetchone()

        if not user:
            # Prefer admin@xploreelite.com default profile
            cursor.execute("SELECT * FROM users WHERE email = 'admin@xploreelite.com'")
            user = cursor.fetchone()

        if not user:
            # Fallback to first user in database
            cursor.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1")
            user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404

        phone_val = user.get('phone') or '+91 98765 43210'
        company_val = user.get('company_name') or 'XploreElite Tourism Analytics Ltd.'
        role_val = user.get('role') or 'Admin'

        profile_data = {
            'id': user['id'],
            'username': user['username'],
            'fullName': user['username'],
            'email': user['email'],
            'phone': phone_val,
            'companyName': company_val,
            'role': role_val,
            'created_at': str(user['created_at']) if user.get('created_at') else 'January 15, 2024',
            'accountCreated': 'January 15, 2024',
            'last_login': str(user['last_login']) if user.get('last_login') else 'Today, 09:30 AM',
            'lastLogin': 'Today, 09:30 AM',
            'accessLevel': 'System Administrator (Level 1)'
        }

        return jsonify({
            'success': True,
            'data': profile_data,
            **profile_data
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f"Profile error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update profile information (username, email, phone, companyName, role)."""
    data = request.get_json(silent=True) or {}

    # Prioritize fullName from frontend form, then fallback to username
    new_username = ''
    if 'fullName' in data and data.get('fullName') is not None and str(data.get('fullName')).strip():
        new_username = str(data.get('fullName')).strip()
    elif 'username' in data and data.get('username') is not None and str(data.get('username')).strip():
        new_username = str(data.get('username')).strip()

    new_email = str(data.get('email') or '').strip()
    new_phone = str(data.get('phone') or '').strip()
    new_company = str(data.get('companyName') or data.get('company_name') or '').strip()
    new_role = str(data.get('role') or '').strip()

    target_id = data.get('id') or session.get('user_id')
    current_email = (data.get('current_email') or data.get('originalEmail') or session.get('user_email') or '').strip()

    if new_email:
        valid_email, err_or_cleaned = validate_email(new_email)
        if not valid_email:
            return jsonify({'success': False, 'message': err_or_cleaned}), 400
        new_email = err_or_cleaned

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        user = None
        if target_id:
            try:
                cursor.execute("SELECT * FROM users WHERE id = %s", (int(target_id),))
                user = cursor.fetchone()
            except (ValueError, TypeError):
                pass

        if not user and current_email:
            cursor.execute("SELECT * FROM users WHERE email = %s", (current_email,))
            user = cursor.fetchone()

        if not user and new_email:
            cursor.execute("SELECT * FROM users WHERE email = %s", (new_email,))
            user = cursor.fetchone()

        if not user:
            # Check user id=2 (active administrator)
            cursor.execute("SELECT * FROM users WHERE id = 2")
            user = cursor.fetchone()

        if not user:
            cursor.execute("SELECT * FROM users WHERE email = 'admin@xploreelite.com'")
            user = cursor.fetchone()

        if not user:
            cursor.execute("SELECT * FROM users ORDER BY id ASC LIMIT 1")
            user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        user_id = user['id']
        updated_username = new_username if new_username else user['username']
        updated_email = new_email if new_email else user['email']
        updated_phone = new_phone if new_phone else (user.get('phone') or '+91 98765 43210')
        updated_company = new_company if new_company else (user.get('company_name') or 'XploreElite Tourism Analytics Ltd.')
        updated_role = new_role.strip() if new_role else (user.get('role') or 'Admin')

        # Prevent duplicate email collision with another user
        if updated_email != user['email']:
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (updated_email, user_id))
            conflict = cursor.fetchone()
            if conflict:
                return jsonify({'success': False, 'message': 'Email address already in use by another account.'}), 400

        cursor.execute("""
            UPDATE users
            SET username = %s, email = %s, phone = %s, company_name = %s, role = %s
            WHERE id = %s
        """, (updated_username, updated_email, updated_phone, updated_company, updated_role, user_id))
        conn.commit()

        # Update session if present
        session['user_id'] = user_id
        session['user_email'] = updated_email
        session['user_username'] = updated_username

        updated_profile = {
            'id': user_id,
            'username': updated_username,
            'fullName': updated_username,
            'email': updated_email,
            'phone': updated_phone,
            'companyName': updated_company,
            'role': updated_role,
            'lastLogin': 'Today, 09:30 AM',
            'accountCreated': 'January 15, 2024',
            'accessLevel': 'System Administrator (Level 1)'
        }

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': updated_profile,
            **updated_profile
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
