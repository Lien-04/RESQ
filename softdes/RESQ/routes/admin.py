"""
Admin Routes - Handle admin dashboard and management functions
"""
from flask import Blueprint, request, jsonify, session

from ..models.user import User, UserRole
from ..models.incident import Incident, IncidentStatus
from ..models.notification import Notification, NotificationType
from ..models.volunteer_skill import VolunteerSkill
from ..db import db
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def require_admin(f):
    """Decorator to require admin role"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        current_user = User.find_by_id(session['user_id'])
        if not current_user or current_user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users', methods=['GET'])
@require_admin
def get_all_users():
    """
    Get all users
    GET /api/admin/users
    """
    role = request.args.get('role')
    
    if role:
        users = User.get_by_role(role)
    else:
        users = User.get_all()
    
    # Include volunteer skills for each user
    users_data = []
    for u in users:
        user_dict = u.to_dict()
        if u.role == UserRole.VOLUNTEER:
            user_dict['volunteer_skills'] = [skill.to_dict() for skill in u.skills_entries]
        else:
            user_dict['volunteer_skills'] = []
        users_data.append(user_dict)
    
    return jsonify({
        'users': users_data
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user(user_id):
    """
    Get specific user
    GET /api/admin/users/<user_id>
    """
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """
    Update user
    PUT /api/admin/users/<user_id>
    """
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
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
        if data['role'] not in [UserRole.CITIZEN, UserRole.VOLUNTEER, UserRole.ADMIN]:
            return jsonify({'error': 'Invalid role'}), 400
        user.role = data['role']
    
    try:
        user.save()
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """
    Delete user
    DELETE /api/admin/users/<user_id>
    """
    current_user = User.find_by_id(session['user_id'])
    
    # Prevent self-deletion
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_statistics():
    """
    Get system statistics
    GET /api/admin/stats
    """
    # User statistics
    all_users = User.get_all()
    total_users = len(all_users)
    
    citizens = User.get_by_role(UserRole.CITIZEN)
    volunteers = User.get_by_role(UserRole.VOLUNTEER)
    admins = User.get_by_role(UserRole.ADMIN)
    
    active_users = len([u for u in all_users if u.is_active])
    
    # Incident statistics
    status_counts = Incident.count_by_status()
    type_counts = Incident.count_by_type()
    total_incidents = sum(status_counts.values())
    
    # Calculate averages
    pending_rate = (status_counts.get('pending', 0) / total_incidents * 100) if total_incidents > 0 else 0
    resolved_rate = (status_counts.get('resolved', 0) / total_incidents * 100) if total_incidents > 0 else 0
    
    return jsonify({
        'users': {
            'total': total_users,
            'active': active_users,
            'by_role': {
                'citizen': len(citizens),
                'volunteer': len(volunteers),
                'admin': len(admins)
            }
        },
        'incidents': {
            'total': total_incidents,
            'by_status': status_counts,
            'by_type': type_counts,
            'rates': {
                'pending': round(pending_rate, 2),
                'resolved': round(resolved_rate, 2)
            }
        }
    }), 200


@admin_bp.route('/incidents', methods=['GET'])
@require_admin
def get_all_incidents():
    """
    Get all incidents with full details
    GET /api/admin/incidents
    """
    status = request.args.get('status')
    exclude_status = request.args.get('exclude_status')
    incident_type = request.args.get('type')
    limit = request.args.get('limit', 100, type=int)

    query = Incident.query
    if status:
        query = query.filter_by(status=status)
    if exclude_status:
        query = query.filter(Incident.status != exclude_status)
    if incident_type:
        query = query.filter_by(incident_type=incident_type)

    incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()

    return jsonify({
        'incidents': [i.to_detailed_dict() for i in incidents]
    }), 200


@admin_bp.route('/incidents/<int:incident_id>', methods=['GET'])
@require_admin
def get_incident(incident_id):
    """
    Get specific incident with full details
    GET /api/admin/incidents/<incident_id>
    """
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    return jsonify({'incident': incident.to_detailed_dict()}), 200


@admin_bp.route('/incidents/<int:incident_id>', methods=['PUT'])
@require_admin
def update_incident(incident_id):
    """
    Update incident (full update)
    PUT /api/admin/incidents/<incident_id>
    """
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    
    # Update all fields
    if 'title' in data:
        incident.title = data['title']
    if 'description' in data:
        incident.description = data['description']
    if 'incident_type' in data:
        incident.incident_type = data['incident_type']
    if 'location' in data:
        incident.location = data['location']
    if 'latitude' in data:
        incident.latitude = data['latitude']
    if 'longitude' in data:
        incident.longitude = data['longitude']
    if 'priority' in data:
        incident.priority = data['priority']
    if 'status' in data:
        incident.status = data['status']
    if 'assigned_to' in data:
        incident.assigned_to = data['assigned_to']
    
    try:
        incident.save()
        return jsonify({
            'message': 'Incident updated successfully',
            'incident': incident.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500


@admin_bp.route('/incidents/<int:incident_id>', methods=['DELETE'])
@require_admin
def delete_incident(incident_id):
    """
    Delete incident
    DELETE /api/admin/incidents/<incident_id>
    """
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    try:
        incident.delete()
        return jsonify({'message': 'Incident deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


@admin_bp.route('/notifications', methods=['GET'])
@require_admin
def get_all_notifications():
    """
    Get all notifications (admin can see alerts)
    GET /api/admin/notifications
    """
    user_id = request.args.get('user_id', type=int)

    if user_id:
        notifications = Notification.get_by_user(user_id)
    else:
        notifications = Notification.get_all(limit=50)

    return jsonify({
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@admin_bp.route('/broadcast', methods=['POST'])
@require_admin
def broadcast_notification():
    """
    Broadcast notification to all users
    POST /api/admin/broadcast
    """
    data = request.get_json()
    
    if not data.get('message'):
        return jsonify({'error': 'Message is required'}), 400
    
    title = data.get('title', 'System Announcement')
    
    # Get all users
    users = User.get_all()
    
    try:
        for user in users:
            Notification.create_notification(
                user_id=user.id,
                incident_id=None,
                title=title,
                message=data['message'],
                notification_type=NotificationType.SYSTEM
            )
        
        return jsonify({
            'message': f'Broadcast sent to {len(users)} users'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Broadcast failed: {str(e)}'}), 500


@admin_bp.route('/volunteers', methods=['GET'])
@require_admin
def get_volunteers_with_skills():
    """
    Get all volunteers with their skills
    GET /api/admin/volunteers
    """
    volunteers = User.get_by_role(UserRole.VOLUNTEER)

    volunteer_data = []
    for vol in volunteers:
        vol_dict = vol.to_dict()

        skills = [skill.to_dict() for skill in VolunteerSkill.query.filter_by(user_id=vol.id).all()]

        vol_dict['volunteer_skills'] = skills
        volunteer_data.append(vol_dict)

    return jsonify({
        'volunteers': volunteer_data
    }), 200


@admin_bp.route('/volunteers/<int:volunteer_id>/skills', methods=['GET'])
@require_admin
def get_volunteer_skills(volunteer_id):
    """
    Get skills for specific volunteer
    GET /api/admin/volunteers/<volunteer_id>/skills
    """
    user = User.find_by_id(volunteer_id)

    if not user or user.role != UserRole.VOLUNTEER:
        return jsonify({'error': 'Volunteer not found'}), 404

    skills = [skill.to_dict() for skill in VolunteerSkill.query.filter_by(user_id=volunteer_id).all()]

    return jsonify({
        'user_id': volunteer_id,
        'username': user.username,
        'full_name': user.full_name,
        'skills': skills
    }), 200


@admin_bp.route('/volunteers/<int:volunteer_id>/skills', methods=['POST'])
@require_admin
def add_volunteer_skill(volunteer_id):
    """
    Add skill to volunteer
    POST /api/admin/volunteers/<volunteer_id>/skills
    """
    user = User.find_by_id(volunteer_id)

    if not user or user.role != UserRole.VOLUNTEER:
        return jsonify({'error': 'Volunteer not found'}), 404

    data = request.get_json()

    if not data.get('skill_name'):
        return jsonify({'error': 'skill_name is required'}), 400

    try:
        skill = VolunteerSkill(
            user_id=volunteer_id,
            skill_name=data['skill_name'],
            proficiency_level=data.get('proficiency_level', 'intermediate')
        )
        skill.save()

        return jsonify({
            'message': 'Skill added successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to add skill: {str(e)}'}), 500
