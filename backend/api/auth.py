from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
from backend.models.user import User
from backend.utils.db import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.get_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'public'),
            phone=data.get('phone')
        )
        user.is_active = True  # Ensure user is active on registration
        user.save()
        
        # Create tokens
        access_token = create_access_token(identity=str(user._id))
        refresh_token = create_refresh_token(identity=str(user._id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        import logging
        logging.exception("Registration failed:")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    import logging
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        logging.warning(f"Login failed: Missing username or password. Data: {data}")
        return jsonify({'error': 'Missing username or password'}), 400
    user = User.get_by_username(data['username'])
    if not user:
        logging.warning(f"Login failed: Username not found: {data.get('username')}")
        return jsonify({'error': 'Invalid username or password'}), 401
    if not user.verify_password(data['password']):
        logging.warning(f"Login failed: Wrong password for user: {data.get('username')}")
        return jsonify({'error': 'Invalid username or password'}), 401
    if not user.is_active:
        logging.warning(f"Login failed: Inactive account for user: {data.get('username')}")
        return jsonify({'error': 'Account is deactivated'}), 403
    access_token = create_access_token(identity=str(user._id))
    refresh_token = create_refresh_token(identity=str(user._id))
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': access_token}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    allowed_fields = ['username', 'phone']
    
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    user.updated_at = datetime.utcnow()
    user.save()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.get_by_id(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing current or new password'}), 400
    
    if not user.verify_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    user.password_hash = user.generate_password_hash(data['new_password'])
    user.updated_at = datetime.utcnow()
    user.save()
    
    return jsonify({'message': 'Password changed successfully'}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a real application, you might want to blacklist the token
    # For now, we'll just return a success message
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@auth_bp.route('/post_login')
def post_login():
    # This route can be used as a redirect after login/register
    return redirect(url_for('user_dashboard'))