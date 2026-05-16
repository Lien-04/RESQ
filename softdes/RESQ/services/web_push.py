"""
Helpers for sending Web Push notifications.
"""
import json
from flask import current_app

from ..db import db
from ..models.push_subscription import PushSubscription


def is_push_configured():
    return bool(
        current_app.config.get('VAPID_PUBLIC_KEY')
        and current_app.config.get('VAPID_PRIVATE_KEY')
    )


def send_notification_pushes(notification):
    """Send a browser push for a saved Notification row."""
    if not is_push_configured():
        return {'sent': 0, 'skipped': True}

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        current_app.logger.warning('pywebpush is not installed; skipping browser push')
        return {'sent': 0, 'skipped': True}

    subscriptions = PushSubscription.query.filter_by(
        user_id=notification.user_id,
        is_active=True
    ).all()

    if not subscriptions:
        return {'sent': 0, 'skipped': False}

    vapid_private_key = current_app.config['VAPID_PRIVATE_KEY'].replace('\\n', '\n')
    vapid_subject = current_app.config.get('VAPID_CLAIM_EMAIL') or 'mailto:admin@resq.local'
    payload = {
        'id': notification.id,
        'title': notification.title,
        'body': notification.message,
        'notification_type': notification.notification_type,
        'incident_id': notification.incident_id,
        'url': f'/reports?id={notification.incident_id}' if notification.incident_id else '/notifications',
    }

    sent = 0
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.to_webpush_subscription_info(),
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={'sub': vapid_subject}
            )
            sent += 1
        except WebPushException as exc:
            status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
            subscription.last_error = str(exc)
            if status_code in (404, 410):
                subscription.is_active = False
            db.session.commit()
            current_app.logger.warning('Web Push failed for subscription %s: %s', subscription.id, exc)
        except Exception as exc:
            subscription.last_error = str(exc)
            db.session.commit()
            current_app.logger.warning('Web Push failed for subscription %s: %s', subscription.id, exc)

    return {'sent': sent, 'skipped': False}
