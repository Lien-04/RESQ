"""
User Model - SQLAlchemy model for users
Using SQLAlchemy ORM for database operations
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import db


class UserRole:
    """User role constants"""
    CITIZEN = 'citizen'
    VOLUNTEER = 'volunteer'
    ADMIN = 'admin'


class User(db.Model):
    """
    User model with role-based attributes
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.CITIZEN)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    skills = db.Column(db.Text)  # comma-separated volunteer skills
    location = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reported_incidents = db.relationship(
        'Incident',
        foreign_keys='Incident.reporter_id',
        back_populates='reporter',
        lazy=True
    )
    assigned_incidents = db.relationship(
        'Incident',
        foreign_keys='Incident.assigned_volunteer_id',
        back_populates='assigned_volunteer',
        lazy=True
    )
    notifications = db.relationship(
        'Notification',
        back_populates='user',
        lazy=True
    )
    skills_entries = db.relationship(
        'VolunteerSkill',
        back_populates='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __init__(self, username, email, password=None, role=UserRole.CITIZEN,
                 full_name=None, phone=None, skills=None, location=None,
                 password_hash=None):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
        elif password_hash:
            self.password_hash = password_hash
        else:
            self.password_hash = ''
        self.role = role
        self.full_name = full_name or username
        self.phone = phone
        self.skills = skills
        self.location = location

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'skills': self.skills,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        return db.session.get(User, user_id)

    @staticmethod
    def get_all():
        """Get all users"""
        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_by_role(role):
        """Get users by role"""
        return User.query.filter_by(role=role).order_by(User.created_at.desc()).all()

    def save(self):
        """Persist the user in the database"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete user from database"""
        db.session.delete(self)
        db.session.commit()
        return True

    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = {
            UserRole.CITIZEN: ['report_incident', 'view_own_reports'],
            UserRole.VOLUNTEER: ['report_incident', 'view_all_reports', 'accept_assignment', 'update_status'],
            UserRole.ADMIN: ['report_incident', 'view_all_reports', 'verify_incident', 'assign_volunteer',
                             'manage_users', 'view_stats', 'delete_incident']
        }
        return permission in permissions.get(self.role, [])

    def matches_skill(self, incident_type):
        """Check whether volunteer skills match the incident type"""
        if not self.skills:
            return False
        normalized_skills = [skill.strip().lower() for skill in self.skills.split(',') if skill.strip()]
        return incident_type.strip().lower() in normalized_skills
    
    def can_report_incident(self):
        """Check if citizen can report incident"""
        return True
    
    def can_verify_incident(self):
        """Citizens cannot verify incidents"""
        return False
    
    def can_assign_volunteer(self):
        """Citizens cannot assign volunteers"""
        return False


class Volunteer(User):
    """
    Volunteer class - Inherits from User
    Can respond to incidents based on skills and location
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = UserRole.VOLUNTEER
        super().__init__(**kwargs)
    
    def can_verify_incident(self):
        """Volunteers can verify incidents"""
        return True
    
    def can_accept_assignment(self):
        """Check if volunteer can accept assignment"""
        return True
    
    def can_update_status(self):
        """Check if volunteer can update incident status"""
        return True
    
    def can_assign_volunteer(self):
        """Volunteers cannot assign volunteers"""
        return False
    
    def matches_skill(self, incident_type):
        """
        Check if volunteer matches required skills for incident
        Simple matching based on skills field
        """
        if not self.skills:
            return False
        volunteer_skills = [s.strip().lower() for s in self.skills.split(',')]
        return incident_type.lower() in volunteer_skills


class Admin(User):
    """
    Admin class - Inherits from User
    Full system access and control
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = UserRole.ADMIN
        super().__init__(**kwargs)
    
    def can_verify_incident(self):
        """Admins can verify incidents"""
        return True
    
    def can_assign_volunteer(self):
        """Admins can assign volunteers"""
        return True
    
    def can_manage_users(self):
        """Check if admin can manage users"""
        return True
    
    def can_view_stats(self):
        """Check if admin can view statistics"""
        return True
    
    def can_delete_incident(self):
        """Check if admin can delete incidents"""
        return True
    
    def can_delete_user(self):
        """Check if admin can delete users"""
        return True
