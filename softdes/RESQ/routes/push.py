"""
Push Notification Routes - Handle Web Push subscriptions and notifications
"""
from flask import Blueprint, request, jsonify, session, current_app
from pywebpush import webpush, WebPushException
import json

from ..models.user import User
from ..models.notification import Notification, NotificationType
from ..models.push_subscription import PushSubscription
from ..db import db

push_bp = Blueprint('push', __name__, url_prefix='/api/push')


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== PUSH SUBSCRIPTION MANAGEMENT ====================

@push_bp.route('/subscribe', methods=['POST'])
@require_auth
def subscribe_to_push():
    """
    Subscribe a device to push notifications
    POST /api/push/subscribe
    Body: {
        "subscription": {
            "endpoint": "https://...",
            "keys": {
                "auth": "...",
                "p256dh": "..."
            }
        },
        "device_name": "Chrome on Windows" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Subscription data is required'}), 400
        
        subscription = data['subscription']
        device_name = data.get('device_name', 'Unknown Device')
        
        # Validate required subscription fields
        if not subscription.get('endpoint') or not subscription.get('keys'):
            return jsonify({'error': 'Invalid subscription format'}), 400
        
        keys = subscription['keys']
        if not keys.get('auth') or not keys.get('p256dh'):
            return jsonify({'error': 'Missing subscription keys'}), 400
        
        # Create or update subscription
        push_sub = PushSubscription.create_subscription(
            user_id=session['user_id'],
            endpoint=subscription['endpoint'],
            auth=keys['auth'],
            p256dh=keys['p256dh'],
            device_name=device_name
        )
        
        return jsonify({
            'message': 'Device subscribed to push notifications',
            'subscription': push_sub.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Subscription failed: {str(e)}'}), 500


@push_bp.route('/unsubscribe', methods=['POST'])
@require_auth
def unsubscribe_from_push():
    """
    Unsubscribe a device from push notifications
    POST /api/push/unsubscribe
    Body: {
        "endpoint": "https://..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'endpoint' not in data:
            return jsonify({'error': 'Endpoint is required'}), 400
        
        push_sub = PushSubscription.find_by_endpoint(data['endpoint'])
        
        if not push_sub:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Verify user owns this subscription
        if push_sub.user_id != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        push_sub.deactivate()
        
        return jsonify({
            'message': 'Device unsubscribed from push notifications'
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Unsubscription failed: {str(e)}'}), 500


@push_bp.route('/subscriptions', methods=['GET'])
@require_auth
def get_user_subscriptions():
    """
    Get all active subscriptions for current user
    GET /api/push/subscriptions
    """
    try:
        subscriptions = PushSubscription.get_by_user(session['user_id'])
        
        return jsonify({
            'subscriptions': [s.to_dict() for s in subscriptions],
            'total': len(subscriptions)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to fetch subscriptions: {str(e)}'}), 500


@push_bp.route('/subscriptions/<int:subscription_id>', methods=['DELETE'])
@require_auth
def delete_subscription(subscription_id):
    """
    Delete a specific subscription
    DELETE /api/push/subscriptions/<subscription_id>
    """
    try:
        push_sub = PushSubscription.find_by_id(subscription_id)
        
        if not push_sub:
            return jsonify({'error': 'Subscription not found'}), 404
        
        # Verify user owns this subscription
        if push_sub.user_id != session['user_id']:
            return jsonify({'error': 'Access denied'}), 403
        
        push_sub.delete()
        
        return jsonify({
            'message': 'Subscription deleted'
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to delete subscription: {str(e)}'}), 500


# ==================== PUSH NOTIFICATION SENDING ====================

@push_bp.route('/send-notification', methods=['POST'])
def send_push_notification():
    """
    Send a push notification to user's subscribed devices
    Can be called internally by notification creation
    POST /api/push/send-notification
    Body: {
        "user_id": 1,
        "title": "Incident Updated",
        "message": "Your incident status changed",
        "data": {...}  (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({'error': 'User ID is required'}), 400
        
        user_id = data['user_id']
        title = data.get('title', 'RESQ Notification')
        message = data.get('message', '')
        payload_data = data.get('data', {})
        
        # Get all active subscriptions for user
        subscriptions = PushSubscription.get_by_user(user_id)
        
        if not subscriptions:
            return jsonify({
                'message': 'No active subscriptions for this user',
                'sent': 0
            }), 200
        
        # Prepare push notification payload
        push_payload = {
            'title': title,
            'message': message,
            'data': payload_data,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        
        sent_count = 0
        failed_count = 0
        
        # Send to each subscription
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        'endpoint': subscription.endpoint,
                        'keys': {
                            'auth': subscription.auth,
                            'p256dh': subscription.p256dh
                        }
                    },
                    data=json.dumps(push_payload),
                    vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
                    vapid_claims={
                        'sub': current_app.config['VAPID_SUBJECT']
                    }
                )
                subscription.update_last_used()
                sent_count += 1
            
            except WebPushException as e:
                # Handle push failures (e.g., expired subscriptions)
                if e.response.status_code == 410:
                    # Gone - subscription is no longer valid
                    subscription.deactivate()
                failed_count += 1
            
            except Exception as e:
                failed_count += 1
        
        return jsonify({
            'message': 'Push notifications sent',
            'sent': sent_count,
            'failed': failed_count,
            'total_subscriptions': len(subscriptions)
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Failed to send push notification: {str(e)}'}), 500


# ==================== VAPID PUBLIC KEY ENDPOINT ====================

@push_bp.route('/vapid-public-key', methods=['GET'])
def get_vapid_public_key():
    """
    Get the public VAPID key for client-side subscription
    GET /api/push/vapid-public-key
    """
    try:
        return jsonify({
            'vapid_public_key': current_app.config['VAPID_PUBLIC_KEY']
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch VAPID key'}), 500
