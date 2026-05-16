self.addEventListener('push', event => {
    let data = {};

    if (event.data) {
        try {
            data = event.data.json();
        } catch (error) {
            data = {
                title: 'RESQ Notification',
                body: event.data.text()
            };
        }
    }

    const title = data.title || 'RESQ Notification';
    const options = {
        body: data.body || data.message || 'You have a new RESQ notification.',
        icon: '/static/images/resq-logo.png',
        badge: '/static/images/resq-logo.png',
        tag: data.id ? `resq-notification-${data.id}` : 'resq-notification',
        data: {
            url: data.url || '/notifications'
        }
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();

    const targetUrl = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : '/notifications';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
            for (const client of clientList) {
                if ('focus' in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }

            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
