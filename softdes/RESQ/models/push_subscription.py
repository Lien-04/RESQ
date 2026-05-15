"""
Push Subscription Model - SQLAlchemy model for storing push notification subscriptions
"""
from datetime import datetime
import hashlib
from ..db import db


class PushSubscription(db.Model):
    """
    Push Subscription model for managing Web Push subscriptions
    Stores browser/device subscription endpoints for each user
    """
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    endpoint = db.Column(db.Text, nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    device_name = db.Column(db.String(100))  # Browser/device name
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='push_subscriptions')

    @staticmethod
    def compute_endpoint_hash(endpoint):
        return hashlib.sha256(endpoint.encode('utf-8')).hexdigest()

    def __init__(self, user_id, endpoint, auth, p256dh, device_name=None):
        self.user_id = user_id
        self.endpoint = endpoint
        self.endpoint_hash = PushSubscription.compute_endpoint_hash(endpoint)
        self.auth = auth
        self.p256dh = p256dh
        self.device_name = device_name or 'Unknown Device'

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'device_name': self.device_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

    def save(self):
        """Persist the subscription in the database"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete subscription from database"""
        db.session.delete(self)
        db.session.commit()
        return True

    @staticmethod
    def find_by_id(subscription_id):
        """Find subscription by ID"""
        return db.session.get(PushSubscription, subscription_id)

    @staticmethod
    def find_by_endpoint(endpoint):
        """Find subscription by endpoint"""
        endpoint_hash = PushSubscription.compute_endpoint_hash(endpoint)
        return PushSubscription.query.filter_by(endpoint_hash=endpoint_hash).first()

    @staticmethod
    def get_by_user(user_id):
        """Get all active subscriptions for a user"""
        return PushSubscription.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).all()

    @staticmethod
    def get_all_active():
        """Get all active subscriptions"""
        return PushSubscription.query.filter_by(is_active=True).all()

    @staticmethod
    def create_subscription(user_id, endpoint, auth, p256dh, device_name=None):
        """Create a new push subscription"""
        # Check if subscription already exists
        existing = PushSubscription.find_by_endpoint(endpoint)
        if existing:
            # Update existing subscription
            existing.is_active = True
            existing.last_used = datetime.utcnow()
            existing.auth = auth
            existing.p256dh = p256dh
            existing.device_name = device_name or existing.device_name
            db.session.commit()
            return existing
        
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            auth=auth,
            p256dh=p256dh,
            device_name=device_name
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription

    def update_last_used(self):
        """Update the last_used timestamp"""
        self.last_used = datetime.utcnow()
        db.session.commit()
        return self

    def deactivate(self):
        """Deactivate the subscription"""
        self.is_active = False
        db.session.commit()
        return self
