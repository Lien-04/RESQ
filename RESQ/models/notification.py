"""
Notification Model - SQLAlchemy model for notifications
"""
from datetime import datetime
from db import db


class NotificationType:
    """Notification type constants"""
    INCIDENT_REPORTED = 'incident_reported'
    STATUS_UPDATE = 'status_update'
    INCIDENT_ASSIGNED = 'incident_assigned'
    INCIDENT_VERIFIED = 'incident_verified'
    BROADCAST = 'broadcast'
    SYSTEM = 'system'


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

    user = db.relationship('User', back_populates='notifications')
    incident = db.relationship('Incident', back_populates='notifications')

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

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def mark_as_read(self):
        self.is_read = True
        db.session.commit()
        return self

    @staticmethod
    def find_by_id(notification_id):
        return db.session.get(Notification, notification_id)

    @staticmethod
    def get_by_user(user_id):
        return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def get_all(limit=50):
        return Notification.query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def create_notification(user_id, title, message, incident_id=None, notification_type=NotificationType.BROADCAST):
        notification = Notification(
            user_id=user_id,
            incident_id=incident_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def mark_all_as_read(user_id):
        notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        if not notifications:
            return True
        for notification in notifications:
            notification.is_read = True
        db.session.commit()
        return True

    @staticmethod
    def notify_incident_reported(user_id, incident_id, title):
        return Notification.create_notification(
            user_id=user_id,
            incident_id=incident_id,
            title='Incident Reported',
            message=f'Your incident "{title}" has been received and is under review.',
            notification_type=NotificationType.INCIDENT_REPORTED
        )

    @staticmethod
    def notify_admins_new_incident(incident_id, title, incident_type, location):
        from models.user import User, UserRole
        admins = User.get_by_role(UserRole.ADMIN)
        for admin in admins:
            Notification.create_notification(
                user_id=admin.id,
                incident_id=incident_id,
                title='New Incident Reported',
                message=f'New {incident_type} incident reported at {location}: "{title}".',
                notification_type=NotificationType.SYSTEM
            )

    @staticmethod
    def notify_status_update(user_id, incident_id, title, status):
        return Notification.create_notification(
            user_id=user_id,
            incident_id=incident_id,
            title='Incident Status Updated',
            message=f'Your incident "{title}" status has been updated to {status}.',
            notification_type=NotificationType.STATUS_UPDATE
        )

    @staticmethod
    def notify_admins_status_update(incident_id, title, status, updated_by_username):
        from models.user import User, UserRole
        admins = User.get_by_role(UserRole.ADMIN)
        for admin in admins:
            Notification.create_notification(
                user_id=admin.id,
                incident_id=incident_id,
                title='Incident Status Changed',
                message=f'Incident "{title}" status changed to {status} by {updated_by_username}.',
                notification_type=NotificationType.SYSTEM
            )

    @staticmethod
    def notify_assignment(user_id, incident_id, title):
        return Notification.create_notification(
            user_id=user_id,
            incident_id=incident_id,
            title='New Assignment',
            message=f'You have been assigned to incident "{title}".',
            notification_type=NotificationType.INCIDENT_ASSIGNED
        )

    @staticmethod
    def notify_incident_verified(user_id, incident_id, title):
        return Notification.create_notification(
            user_id=user_id,
            incident_id=incident_id,
            title='Incident Verified',
            message=f'Your incident "{title}" has been verified by an administrator.',
            notification_type=NotificationType.INCIDENT_VERIFIED
        )