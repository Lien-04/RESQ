"""
User Model - SQLAlchemy model for users
Using SQLAlchemy ORM for database operations
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from db import db


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
    skills = db.Column(db.Text)  # JSON string for skills
    location = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - specify foreign_keys to avoid ambiguity
    reported_incidents = db.relationship('Incident', foreign_keys='Incident.reporter_id', backref='reporter_user')
    assigned_incidents = db.relationship('Incident', foreign_keys='Incident.assigned_volunteer_id', backref='assigned_volunteer_user')
    notifications = db.relationship('Notification', backref='notified_user', lazy=True)
    
    def __init__(self, username, email, password, role=UserRole.CITIZEN, 
                 full_name=None, phone=None, skills=None, location=None):
        self.username = username
        self.email = email
        self.set_password(password)
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
        return User.query.get(user_id)
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        return User.query.all()
    
    @staticmethod
    def get_users_by_role(role):
        """Get users by role"""
        return User.query.filter_by(role=role).all()
    def get_db():
        """Get database connection"""
        if 'db' not in g:
            g.db = sqlite3.connect('resq.db')
            g.db.row_factory = sqlite3.Row
        return g.db
    
    @staticmethod
    def close_db(exception=None):
        """Close database connection"""
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    def to_dict(self):
        """Convert user object to dictionary"""
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
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at)
        }
    
    def save(self):
        """Save user to database"""
        db = self.get_db()
        cursor = db.cursor()
        
        if self.id:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET username=?, email=?, password_hash=?, role=?, full_name=?,
                    phone=?, skills=?, location=?, is_active=?, updated_at=?
                WHERE id=?
            ''', (self.username, self.email, self.password_hash, self.role, self.full_name,
                  self.phone, self.skills, self.location, self.is_active,
                  datetime.now().isoformat(), self.id))
        else:
            # Insert new user
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, full_name,
                                  phone, skills, location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.username, self.email, self.password_hash, self.role, self.full_name,
                  self.phone, self.skills, self.location, datetime.now().isoformat(), datetime.now().isoformat()))
            self.id = cursor.lastrowid
        
        db.commit()
        return self
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        db = User.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        db = User.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        db = User.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def get_all():
        """Get all users"""
        db = User.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        return [User(**dict(row)) for row in rows]
    
    @staticmethod
    def get_by_role(role):
        """Get users by role"""
        db = User.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE role = ? ORDER BY created_at DESC', (role,))
        rows = cursor.fetchall()
        
        return [User(**dict(row)) for row in rows]
    
    def delete(self):
        """Delete user from database"""
        if self.id:
            db = self.get_db()
            cursor = db.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (self.id,))
            db.commit()
            return True
        return False
    
    def has_permission(self, permission):
        """
        Check if user has specific permission
        Override in subclasses
        """
        permissions = {
            'citizen': ['report_incident', 'view_own_reports'],
            'volunteer': ['report_incident', 'view_all_reports', 'accept_assignment', 'update_status'],
            'admin': ['report_incident', 'view_all_reports', 'verify_incident', 'assign_volunteer', 
                     'manage_users', 'view_stats', 'delete_incident']
        }
        return permission in permissions.get(self.role, [])


class Citizen(User):
    """
    Citizen class - Inherits from User
    Can report incidents and view own reports
    """
    
    def __init__(self, **kwargs):
        kwargs['role'] = UserRole.CITIZEN
        super().__init__(**kwargs)
    
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
