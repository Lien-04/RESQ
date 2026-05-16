"""
Push subscription model for browser Web Push notifications.
"""
from datetime import datetime
from ..db import db


class PushSubscription(db.Model):
    """Stores a browser/device push subscription for a logged-in user."""
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(500), nullable=False, unique=True)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    user_agent = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_webpush_subscription_info(self):
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth,
            }
        }

    @staticmethod
    def upsert(user_id, subscription_info, user_agent=None):
        endpoint = subscription_info.get('endpoint')
        keys = subscription_info.get('keys') or {}
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            raise ValueError('Invalid push subscription')

        subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if subscription:
            subscription.user_id = user_id
            subscription.p256dh = p256dh
            subscription.auth = auth
            subscription.user_agent = user_agent
            subscription.is_active = True
            subscription.last_error = None
        else:
            subscription = PushSubscription(
                user_id=user_id,
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                user_agent=user_agent
            )
            db.session.add(subscription)

        db.session.commit()
        return subscription

    @staticmethod
    def deactivate_endpoint(endpoint, error=None):
        subscription = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if subscription:
            subscription.is_active = False
            subscription.last_error = error
            db.session.commit()
        return subscription
