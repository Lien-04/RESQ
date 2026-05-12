"""
Notification Model - SQLAlchemy model for notifications
"""
from datetime import datetime
from db import db


class NotificationType:
    """Notification type constants"""
    INCIDENT_REPORTED = 'incident_reported'
    INCIDENT_UPDATED = 'incident_updated'
    INCIDENT_ASSIGNED = 'incident_assigned'
    BROADCAST = 'broadcast'


class Notification(db.Model):
    """
    Notification model for system alerts
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'))
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    incident = db.relationship('Incident')
    
    def __init__(self, user_id, notification_type, title, message, incident_id=None):
        self.user_id = user_id
        self.incident_id = incident_id
        self.notification_type = notification_type
        self.title = title
        self.message = message
    
    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'incident_id': self.incident_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_user_notifications(user_id):
        """Get notifications for a user"""
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def get_unread_notifications(user_id):
        """Get unread notifications for a user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False