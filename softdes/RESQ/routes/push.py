"""
Routes for browser Web Push subscriptions.
"""
from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError

from ..db import db
from ..models.push_subscription import PushSubscription
from ..models.notification import Notification, NotificationType
from ..services.web_push import is_push_configured


push_bp = Blueprint('push', __name__, url_prefix='/api/push')


def require_auth(f):
    """Decorator to require authentication."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@push_bp.route('/public-key', methods=['GET'])
@require_auth
def get_public_key():
    public_key = current_app.config.get('VAPID_PUBLIC_KEY')
    if not public_key:
        return jsonify({
            'enabled': False,
            'error': 'Web Push is not configured'
        }), 503

    return jsonify({
        'enabled': True,
        'public_key': public_key
    }), 200


@push_bp.route('/subscribe', methods=['POST'])
@require_auth
def subscribe():
    data = request.get_json(silent=True) or {}

    try:
        subscription = PushSubscription.upsert(
            user_id=session['user_id'],
            subscription_info=data,
            user_agent=request.headers.get('User-Agent')
        )
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Database error while saving push subscription')
        return jsonify({'error': 'Database error while saving push subscription'}), 500
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Unexpected error while saving push subscription')
        return jsonify({'error': 'Unexpected error while saving push subscription'}), 500

    return jsonify({
        'message': 'Push notifications enabled',
        'subscription_id': subscription.id
    }), 201


@push_bp.route('/test', methods=['POST'])
@require_auth
def test_push():
    active_count = PushSubscription.query.filter_by(
        user_id=session['user_id'],
        is_active=True
    ).count()

    if not is_push_configured():
        return jsonify({
            'error': 'Web Push is not configured',
            'active_subscriptions': active_count
        }), 503

    if active_count == 0:
        return jsonify({
            'error': 'No active push subscription for this user',
            'active_subscriptions': 0
        }), 400

    notification = Notification.create_notification(
        user_id=session['user_id'],
        title='RESQ Push Test',
        message='Device push notifications are enabled for this account.',
        notification_type=NotificationType.SYSTEM
    )

    return jsonify({
        'message': 'Test push processed',
        'notification_id': notification.id,
        'active_subscriptions': active_count,
        'push_result': getattr(notification, 'push_result', None)
    }), 200


@push_bp.route('/unsubscribe', methods=['POST'])
@require_auth
def unsubscribe():
    data = request.get_json(silent=True) or {}
    endpoint = data.get('endpoint')

    if not endpoint:
        return jsonify({'error': 'Missing endpoint'}), 400

    PushSubscription.deactivate_endpoint(endpoint)
    return jsonify({'message': 'Push notifications disabled'}), 200
