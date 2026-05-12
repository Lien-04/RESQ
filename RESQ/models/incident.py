"""
Incident Model - SQLAlchemy model for incidents
"""
from datetime import datetime
from db import db


class IncidentStatus:
    """Incident status constants"""
    PENDING = 'pending'
    VERIFIED = 'verified'
    IN_PROGRESS = 'in_progress'
    RESOLVED = 'resolved'


class IncidentType:
    """Incident type constants"""
    FIRE = 'fire'
    FLOOD = 'flood'
    EARTHQUAKE = 'earthquake'
    STORM = 'storm'
    MEDICAL = 'medical'
    TRAFFIC = 'traffic'
    OTHER = 'other'


class Incident(db.Model):
    """
    Incident model for disaster reports
    """
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    incident_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, critical
    status = db.Column(db.String(20), default=IncidentStatus.PENDING)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_volunteer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Relationships - specify foreign_keys to avoid ambiguity
    reporter = db.relationship('User', foreign_keys=[reporter_id])
    assigned_volunteer = db.relationship('User', foreign_keys=[assigned_volunteer_id])
    
    def __init__(self, title, description, incident_type, location, reporter_id,
                 latitude=None, longitude=None, priority='normal'):
        self.title = title
        self.description = description
        self.incident_type = incident_type
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.priority = priority
        self.reporter_id = reporter_id
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'incident_type': self.incident_type,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'priority': self.priority,
            'status': self.status,
            'reporter_id': self.reporter_id,
            'assigned_volunteer_id': self.assigned_volunteer_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    @staticmethod
    def get_all_incidents():
        """Get all incidents"""
        return Incident.query.all()
    
    @staticmethod
    def get_incidents_by_status(status):
        """Get incidents by status"""
        return Incident.query.filter_by(status=status).all()
    
    @staticmethod
    def get_incidents_by_type(incident_type):
        """Get incidents by type"""
        return Incident.query.filter_by(incident_type=incident_type).all()
    
    @staticmethod
    def find_by_id(incident_id):
        """Find incident by ID"""
        return Incident.query.get(incident_id)