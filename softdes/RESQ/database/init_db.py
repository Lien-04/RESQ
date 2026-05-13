"""
Database Initialization Script
Creates tables and initializes sample data
"""
from datetime import datetime
from ..db import db
from ..models.user import User, UserRole
from ..models.incident import Incident
from ..models.notification import Notification, NotificationType
from ..models.volunteer_skill import VolunteerSkill


def init_database():
    """Initialize the database with sample data"""
    if User.query.count() > 0:
        return {'status': 'already_initialized'}

    sample_users = [
        {
            'username': 'admin',
            'email': 'admin@resq.org',
            'password': 'admin123',
            'role': UserRole.ADMIN,
            'full_name': 'System Administrator',
            'phone': '555-0100',
            'skills': 'management,coordination',
            'location': 'Headquarters'
        },
        {
            'username': 'john_volunteer',
            'email': 'john@resq.org',
            'password': 'volunteer123',
            'role': UserRole.VOLUNTEER,
            'full_name': 'John Smith',
            'phone': '555-0101',
            'skills': 'medical,fire-fighting',
            'location': 'Downtown'
        },
        {
            'username': 'sarah_volunteer',
            'email': 'sarah@resq.org',
            'password': 'volunteer123',
            'role': UserRole.VOLUNTEER,
            'full_name': 'Sarah Johnson',
            'phone': '555-0102',
            'skills': 'search-and-rescue,first-aid',
            'location': 'Westside'
        },
        {
            'username': 'mike_citizen',
            'email': 'mike@resq.org',
            'password': 'citizen123',
            'role': UserRole.CITIZEN,
            'full_name': 'Mike Wilson',
            'phone': '555-0103',
            'skills': None,
            'location': 'Northside'
        },
        {
            'username': 'emma_citizen',
            'email': 'emma@resq.org',
            'password': 'citizen123',
            'role': UserRole.CITIZEN,
            'full_name': 'Emma Davis',
            'phone': '555-0104',
            'skills': None,
            'location': 'Eastside'
        }
    ]

    created_users = {}
    for user_data in sample_users:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            role=user_data['role'],
            full_name=user_data['full_name'],
            phone=user_data['phone'],
            skills=user_data['skills'],
            location=user_data['location']
        )
        user.save()
        created_users[user.username] = user

    volunteer_skills = {
        'john_volunteer': ['medical', 'fire-fighting'],
        'sarah_volunteer': ['search-and-rescue', 'first-aid']
    }

    for username, skills in volunteer_skills.items():
        user = created_users.get(username)
        if not user:
            continue
        for skill_name in skills:
            skill = VolunteerSkill(
                user_id=user.id,
                skill_name=skill_name,
                proficiency_level='intermediate'
            )
            skill.save()

    sample_incidents = [
        {
            'title': 'Building Fire Downtown',
            'description': 'Multi-story building showing smoke from upper floors.',
            'incident_type': 'fire',
            'location': '123 Main Street, Downtown'
        },
        {
            'title': 'Flash Flooding on Oak Avenue',
            'description': 'Street flooding due to heavy rainfall.',
            'incident_type': 'flood',
            'location': 'Oak Avenue & 5th Street'
        },
        {
            'title': 'Traffic Accident at Intersection',
            'description': 'Two-vehicle collision. One driver injured.',
            'incident_type': 'traffic',
            'location': 'Broadway & 42nd Street'
        },
        {
            'title': 'Power Lines Down',
            'description': 'Storm has knocked down power lines blocking road.',
            'incident_type': 'storm',
            'location': 'Elm Street near park'
        },
        {
            'title': 'Minor Earthquake Rumors',
            'description': 'Residents reporting tremors.',
            'incident_type': 'earthquake',
            'location': 'Various locations'
        }
    ]

    created_incidents = []
    reporter = created_users.get('mike_citizen')

    for incident_data in sample_incidents:
        incident = Incident(
            title=incident_data['title'],
            description=incident_data['description'],
            incident_type=incident_data['incident_type'],
            location=incident_data['location'],
            reporter_id=reporter.id
        )
        incident.save()
        created_incidents.append(incident)

    if created_incidents:
        Notification.notify_incident_reported(
            reporter.id,
            created_incidents[0].id,
            created_incidents[0].title
        )
        Notification.notify_assignment(
            created_users['john_volunteer'].id,
            created_incidents[0].id,
            created_incidents[0].title
        )

    return {
        'users': len(sample_users),
        'incidents': len(created_incidents)
    }


if __name__ == '__main__':
    from app import create_app
    app = create_app('development')
    with app.app_context():
        init_database()

    print('\nRun: python app.py')
