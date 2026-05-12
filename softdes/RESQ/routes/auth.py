"""
Authentication Routes - Handle user registration, login, and logout
"""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import re

from ..models.user import User, UserRole
from ..models.volunteer_skill import VolunteerSkill

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength (min 6 characters)"""
    return len(password) >= 6


def validate_username(username):
    """Validate username ( alphanumeric and underscore, 3-20 chars)"""
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    POST /api/register
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name', 'role']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate role
    valid_roles = [UserRole.CITIZEN, UserRole.VOLUNTEER, UserRole.ADMIN]
    if data['role'] not in valid_roles:
        return jsonify({'error': f'Invalid role. Must be one of: {valid_roles}'}), 400
    
    # Validate email format
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    if not validate_password(data['password']):
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Validate username
    if not validate_username(data['username']):
        return jsonify({'error': 'Username must be 3-20 alphanumeric characters'}), 400
    
    # Check if username already exists
    if User.find_by_username(data['username']):
        return jsonify({'error': 'Username already exists'}), 409
    
    # Check if email already exists
    if User.find_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data['role'],
        full_name=data['full_name'],
        phone=data.get('phone'),
        skills=data.get('skills'),
        location=data.get('location')
    )
    
    try:
        user.save()

        # If volunteer, add skills to volunteer_skills table
        if data['role'] == 'volunteer' and data.get('skills'):
            skills_list = [skill.strip() for skill in data['skills'].split(',') if skill.strip()]
            for skill in skills_list:
                VolunteerSkill(
                    user_id=user.id,
                    skill_name=skill,
                    proficiency_level='intermediate'
                ).save()

        # Set session for auto-login
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    POST /api/login
    """
    data = request.get_json()

    # Validate required fields
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400

    # Find user by username
    user = User.find_by_username(data['username'])

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check password
    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check if user is active
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403

    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user
    POST /api/logout
    """
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current logged in user
    GET /api/me
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.find_by_id(session['user_id'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/users', methods=['GET'])
def get_users():
    """
    Get all users (admin only)
    GET /api/users
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = User.find_by_id(session['user_id'])
    
    if not current_user or current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.get_all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update user (admin only)
    PUT /api/users/<user_id>
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = User.find_by_id(session['user_id'])
    
    if not current_user or current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'location' in data:
        user.location = data['location']
    if 'skills' in data:
        user.skills = data['skills']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'role' in data:
        user.role = data['role']
    
    try:
        user.save()
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete user (admin only)
    DELETE /api/users/<user_id>
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = User.find_by_id(session['user_id'])
    
    if not current_user or current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent self-deletion
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    try:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500
