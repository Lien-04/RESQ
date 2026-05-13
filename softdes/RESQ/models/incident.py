"""
Incident Model - SQLAlchemy model for incidents
"""
from datetime import datetime
from sqlalchemy import func
from ..db import db


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

    TYPES = [FIRE, FLOOD, EARTHQUAKE, STORM, MEDICAL, TRAFFIC, OTHER]


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
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    reporter = db.relationship('User', foreign_keys=[reporter_id], back_populates='reported_incidents')
    assigned_volunteer = db.relationship('User', foreign_keys=[assigned_volunteer_id], back_populates='assigned_incidents')
    verifier = db.relationship('User', foreign_keys=[verified_by])
    notifications = db.relationship('Notification', back_populates='incident', lazy=True)

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

    @property
    def reported_by(self):
        return self.reporter_id

    @property
    def assigned_to(self):
        return self.assigned_volunteer_id

    @assigned_to.setter
    def assigned_to(self, volunteer_id):
        self.assigned_volunteer_id = volunteer_id

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
            'verified_by': self.verified_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

    def to_detailed_dict(self):
        data = self.to_dict()
        data.update({
            'reporter': self.reporter.username if self.reporter else None,
            'assigned_volunteer': self.assigned_volunteer.username if self.assigned_volunteer else None,
            'verified_by_username': self.verifier.username if self.verifier else None
        })
        return data

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return True

    @staticmethod
    def find_by_id(incident_id):
        return db.session.get(Incident, incident_id)

    @staticmethod
    def get_by_user(user_id):
        return Incident.query.filter_by(reporter_id=user_id).order_by(Incident.created_at.desc()).all()

    @staticmethod
    def get_assigned_to(volunteer_id):
        return Incident.query.filter_by(assigned_volunteer_id=volunteer_id).order_by(Incident.created_at.desc()).all()

    @staticmethod
    def get_completed_assignments(volunteer_id):
        return Incident.query.filter_by(
            assigned_volunteer_id=volunteer_id,
            status=IncidentStatus.RESOLVED
        ).order_by(Incident.resolved_at.desc()).all()

    @staticmethod
    def get_all(status=None, incident_type=None, assigned_to=None, limit=100):
        query = Incident.query
        if status:
            query = query.filter_by(status=status)
        if incident_type:
            query = query.filter_by(incident_type=incident_type)
        if assigned_to is not None:
            query = query.filter_by(assigned_volunteer_id=assigned_to)
        return query.order_by(Incident.created_at.desc()).limit(limit).all()

    @staticmethod
    def count_by_status():
        results = db.session.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).all()
        return {status: count for status, count in results}

    @staticmethod
    def count_by_type():
        results = db.session.query(Incident.incident_type, func.count(Incident.id)).group_by(Incident.incident_type).all()
        return {incident_type: count for incident_type, count in results}

    def update_status(self, new_status, updated_by=None):
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status == IncidentStatus.RESOLVED:
            self.resolved_at = datetime.utcnow()
        if updated_by is not None:
            self.verified_by = updated_by
        db.session.commit()
        return self

    def assign_to(self, volunteer_id):
        self.assigned_volunteer_id = volunteer_id
        if self.status == IncidentStatus.PENDING:
            self.status = IncidentStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self

    def verify(self, admin_id):
        self.status = IncidentStatus.VERIFIED
        self.verified_by = admin_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
