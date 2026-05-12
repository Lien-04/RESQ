"""
Incident Routes - Handle incident reporting, tracking, and management
Implemented permissions:
- Citizen, Volunteer & Admin: Can CREATE incident reports
- Admin only: Can UPDATE incident status
- Admin: Can see volunteer skills and list
- Volunteer & Admin: Can VIEW all reports
- Notifications: Available to Volunteer and Admin
"""
from flask import Blueprint, request, jsonify, session, g

from models.user import User, UserRole
from models.incident import Incident, IncidentStatus, IncidentType
from models.notification import Notification, NotificationType
from db import db

incidents_bp = Blueprint('incidents', __name__, url_prefix='/api')


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


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


# ==================== INCIDENT REPORTING ====================
# Citizen & Volunteer can report incidents
@incidents_bp.route('/reports', methods=['POST'])
@require_auth
def create_incident():
    """
    Create new incident report
    POST /api/reports
    Citizen & Volunteer can create reports
    """
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description', 'incident_type', 'location']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate incident type
    if data['incident_type'] not in IncidentType.TYPES:
        return jsonify({'error': f'Invalid incident type. Must be one of: {IncidentType.TYPES}'}), 400
    
    current_user = User.find_by_id(session['user_id'])
    
# Citizen, Volunteer, and Admin can report
    if current_user.role not in [UserRole.CITIZEN, UserRole.VOLUNTEER, UserRole.ADMIN]:
        return jsonify({'error': 'Only citizens, volunteers, and admins can report incidents'}), 403
    
    # Create incident
    incident = Incident(
        title=data['title'],
        description=data['description'],
        incident_type=data['incident_type'],
        location=data['location'],
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        priority=data.get('priority', 'normal'),
        reported_by=session['user_id']
    )
    
    try:
        incident.save()
        
        # Create notification for reporter
        Notification.notify_incident_reported(
            session['user_id'],
            incident.id,
            incident.title
        )
        
        # Notify all admins of new incident
        Notification.notify_admins_new_incident(
            incident.id,
            incident.title,
            incident.incident_type,
            incident.location
        )
        
        return jsonify({
            'message': 'Incident reported successfully',
            'incident': incident.to_dict()
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Failed to create incident: {str(e)}'}), 500


# ==================== VIEW REPORTS ====================
# Volunteer & Admin can view all reports
@incidents_bp.route('/reports', methods=['GET'])
@require_auth
def get_incidents():
    """
    Get all incidents with optional filtering
    GET /api/reports?status=pending&type=fire&assigned_to_me=true
    Volunteer & Admin can view all reports
    """
    status = request.args.get('status')
    incident_type = request.args.get('type')
    status = request.args.get('status')
    incident_type = request.args.get('type')
    assigned_to_me = request.args.get('assigned_to_me', '').lower() == 'true'
    my_reports = request.args.get('my_reports', '').lower() == 'true'
    completed_assignments = request.args.get('completed_assignments', '').lower() == 'true'
    limit = request.args.get('limit', 100, type=int)
    
    current_user = User.find_by_id(session['user_id'])
    
    # Priority: completed_assignments > assigned_to_me > my_reports > all
    if completed_assignments:
        if current_user.role != UserRole.VOLUNTEER:
            return jsonify({'error': 'Only volunteers can view completed assignments'}), 403
        incidents = Incident.get_completed_assignments(session['user_id'])
    elif assigned_to_me:
        if current_user.role != UserRole.VOLUNTEER:
            return jsonify({'error': 'Only volunteers can view assigned incidents'}), 403
        incidents = Incident.get_assigned_to(session['user_id'])
    elif my_reports:
        incidents = Incident.get_by_user(session['user_id'])
    else:
        # All authenticated users can view all reports
        incidents = Incident.get_all(status=status, incident_type=incident_type, limit=limit)
    
    return jsonify({
        'incidents': [i.to_detailed_dict() for i in incidents]
    }), 200


@incidents_bp.route('/reports/<int:incident_id>', methods=['GET'])
@require_auth
def get_incident(incident_id):
    """Get specific incident"""
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    # All authenticated users can view incident details
    return jsonify({'incident': incident.to_detailed_dict()}), 200


# ==================== UPDATE INCIDENT ====================
@incidents_bp.route('/reports/<int:incident_id>', methods=['PUT'])
@require_auth
def update_incident(incident_id):
    """Update incident details"""
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    current_user = User.find_by_id(session['user_id'])
    
    # Only Admin can update incident details
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
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
    
    try:
        incident.save()
        return jsonify({
            'message': 'Incident updated successfully',
            'incident': incident.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Update failed: {str(e)}'}), 500


@incidents_bp.route('/reports/<int:incident_id>', methods=['DELETE'])
@require_auth
def delete_incident(incident_id):
    """Delete incident"""
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    current_user = User.find_by_id(session['user_id'])
    
    # Only Admin can delete
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        incident.delete()
        return jsonify({'message': 'Incident deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


# ==================== UPDATE STATUS ====================
# Admin can always update status, Volunteers can only update verified incidents
@incidents_bp.route('/reports/<int:incident_id>/status', methods=['PUT'])
@require_auth
def update_incident_status(incident_id):
    """
    Update incident status
    PUT /api/reports/<incident_id>/status
    Admins can always update. Volunteers can only update verified incidents.
    """
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    # Validate status
    valid_statuses = [IncidentStatus.PENDING, IncidentStatus.VERIFIED, 
                    IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED]
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
    
    current_user = User.find_by_id(session['user_id'])
    
    # Admin can always update
    if current_user.role == UserRole.ADMIN:
        try:
            incident.update_status(new_status, session['user_id'])
            
            # Send notification to reporter
            Notification.notify_status_update(
                incident.reported_by,
                incident.id,
                incident.title,
                new_status
            )
            
            # Notify all admins of status change
            Notification.notify_admins_status_update(
                incident.id,
                incident.title,
                new_status,
                current_user.username
            )
            
            return jsonify({
                'message': 'Status updated successfully',
                'incident': incident.to_dict()
            }), 200
        except Exception as e:
            return jsonify({'error': f'Update failed: {str(e)}'}), 500
    
    # Volunteers can only update if incident is verified and assigned to them
    elif current_user.role == UserRole.VOLUNTEER:
        if not incident.verified_by:
            return jsonify({'error': 'Report must be verified before updating status. Please wait for admin verification.'}), 400
        
        if incident.assigned_to != session['user_id']:
            return jsonify({'error': 'This incident is not assigned to you'}), 403
        
        try:
            incident.update_status(new_status, session['user_id'])
            
            # Send notification to reporter
            Notification.notify_status_update(
                incident.reported_by,
                incident.id,
                incident.title,
                new_status
            )
            
            # Notify all admins of status change
            Notification.notify_admins_status_update(
                incident.id,
                incident.title,
                new_status,
                current_user.username
            )
            
            return jsonify({
                'message': 'Status updated successfully',
                'incident': incident.to_dict()
            }), 200
        except Exception as e:
            return jsonify({'error': f'Update failed: {str(e)}'}), 500
    
    else:
        return jsonify({'error': 'Only Admin and assigned Volunteers can update incident status'}), 403


# ==================== VERIFY INCIDENT ====================
# Admin only
@incidents_bp.route('/reports/<int:incident_id>/verify', methods=['POST'])
@require_auth
def verify_incident(incident_id):
    """
    Verify incident
    POST /api/reports/<incident_id>/verify
    Admin only
    """
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    current_user = User.find_by_id(session['user_id'])
    
    # Only Admin can verify
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        incident.verify(session['user_id'])
        
        # Notify reporter
        Notification.notify_incident_verified(
            incident.reported_by,
            incident.id,
            incident.title
        )
        
        return jsonify({
            'message': 'Incident verified successfully',
            'incident': incident.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500


# ==================== ASSIGN INCIDENT ====================
# Admin only
@incidents_bp.route('/reports/<int:incident_id>/assign', methods=['POST'])
@require_auth
def assign_incident(incident_id):
    """Assign incident to volunteer - Admin only"""
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    data = request.get_json()
    volunteer_id = data.get('volunteer_id')
    
    if not volunteer_id:
        return jsonify({'error': 'Volunteer ID is required'}), 400
    
    current_user = User.find_by_id(session['user_id'])
    
    # Only Admin can assign
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Verify volunteer exists and is a volunteer
    volunteer = User.find_by_id(volunteer_id)
    if not volunteer or volunteer.role != UserRole.VOLUNTEER:
        return jsonify({'error': 'Invalid volunteer'}), 404
    
    try:
        incident.assign_to(volunteer_id)
        
        # Notify volunteer
        Notification.notify_assignment(
            volunteer_id,
            incident.id,
            incident.title
        )
        
        return jsonify({
            'message': 'Incident assigned successfully',
            'incident': incident.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Assignment failed: {str(e)}'}), 500


# ==================== VOLUNTEER MANAGEMENT ====================
# Admin only - see volunteers with skills
@incidents_bp.route('/volunteers', methods=['GET'])
@require_auth
def get_volunteers():
    """
    Get available volunteers with skills
    GET /api/volunteers
    Admin only
    """
    current_user = User.find_by_id(session['user_id'])
    
    # Only Admin can see volunteer list
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    volunteers = User.get_by_role(UserRole.VOLUNTEER)
    
    return jsonify({
        'volunteers': [v.to_dict() for v in volunteers]
    }), 200


# Admin only - find matching volunteers
@incidents_bp.route('/volunteers/matching', methods=['GET'])
@require_auth
def get_matching_volunteers():
    """
    Get matching volunteers for an incident
    GET /api/volunteers/matching?incident_id=<id>
    Admin only
    """
    incident_id = request.args.get('incident_id', type=int)
    
    if not incident_id:
        return jsonify({'error': 'Incident ID is required'}), 400
    
    incident = Incident.find_by_id(incident_id)
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    
    current_user = User.find_by_id(session['user_id'])
    
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get all volunteers
    volunteers = User.get_by_role(UserRole.VOLUNTEER)
    
    # Skill-based matching
    matching = []
    for volunteer in volunteers:
        if volunteer.matches_skill(incident.incident_type):
            matching.append(volunteer.to_dict())
    
    # If no skill match, return all volunteers
    if not matching:
        matching = [v.to_dict() for v in volunteers]
    
    return jsonify({
        'volunteers': matching,
        'incident': incident.to_dict()
    }), 200


# ==================== NOTIFICATIONS ====================
# For all users
@incidents_bp.route('/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """
    Get notifications for current user
    GET /api/notifications
    Available for all users (Citizen, Volunteer, Admin)
    """
    notifications = Notification.get_by_user(session['user_id'])
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@incidents_bp.route('/notifications/unread', methods=['GET'])
@require_auth
def get_unread_notifications():
    """Get unread notifications count - for all users"""
    count = Notification.get_unread_count(session['user_id'])
    
    return jsonify({'unread_count': count}), 200


@incidents_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@require_auth
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification = Notification.find_by_id(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if notification.user_id != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403
    
    notification.mark_as_read()
    
    return jsonify({
        'message': 'Notification marked as read',
        'notification': notification.to_dict()
    }), 200


@incidents_bp.route('/notifications/mark-all-read', methods=['POST'])
@require_auth
def mark_all_notifications_read():
    """
    Mark ALL notifications as read for current user
    POST /api/notifications/mark-all-read
    """
    success = Notification.mark_all_as_read(session['user_id'])
    
    if success:
        return jsonify({
            'message': 'All notifications marked as read'
        }), 200
    else:
        return jsonify({'error': 'Failed to mark notifications as read'}), 500


# ==================== STATISTICS ====================
# Admin only
@incidents_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """Get incident statistics - Admin only"""
    current_user = User.find_by_id(session['user_id'])
    
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Admin access required'}), 403
    
    status_counts = Incident.count_by_status()
    type_counts = Incident.count_by_type()
    total_incidents = sum(status_counts.values())
    total_users = len(User.get_all())
    total_volunteers = len(User.get_by_role(UserRole.VOLUNTEER))
    
    return jsonify({
        'total_incidents': total_incidents,
        'total_users': total_users,
        'total_volunteers': total_volunteers,
        'by_status': status_counts,
        'by_type': type_counts
    }), 200
