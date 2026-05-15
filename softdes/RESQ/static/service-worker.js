/**
 * Service Worker for RESQ Push Notifications
 * Handles push events even when the app is not open
 */

const CACHE_NAME = 'resq-cache-v1';

// Install event - cache essential files
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Service Worker] Caching essential files');
            return cache.addAll([
                '/',
                '/static/css/style.css'
            ]).catch(err => {
                console.log('[Service Worker] Cache add error (non-critical):', err);
            });
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push notification received');
    
    try {
        let notificationData = {
            title: 'RESQ Notification',
            body: 'You have a new notification',
            icon: '/static/images/resq-logo.png',
            badge: '/static/images/resq-logo.png',
            tag: 'resq-notification',
            requireInteraction: false
        };
        
        // Parse push data if available
        if (event.data) {
            try {
                const data = event.data.json();
                notificationData.title = data.title || notificationData.title;
                notificationData.body = data.message || notificationData.body;
                notificationData.data = {
                    url: data.data?.url || '/notifications',
                    ...data.data
                };
            } catch (e) {
                console.log('[Service Worker] Could not parse push data:', e);
                notificationData.body = event.data.text();
            }
        }
        
        event.waitUntil(
            self.registration.showNotification(
                notificationData.title,
                {
                    body: notificationData.body,
                    icon: notificationData.icon,
                    badge: notificationData.badge,
                    tag: notificationData.tag,
                    requireInteraction: notificationData.requireInteraction,
                    data: notificationData.data || {},
                    // Add action buttons for critical notifications
                    actions: [
                        {
                            action: 'open',
                            title: 'Open',
                            icon: '/static/images/resq-logo.png'
                        },
                        {
                            action: 'close',
                            title: 'Close',
                            icon: '/static/images/resq-logo.png'
                        }
                    ]
                }
            )
        );
    } catch (error) {
        console.error('[Service Worker] Error handling push:', error);
        event.waitUntil(
            self.registration.showNotification('RESQ Alert', {
                body: 'You have a new notification. Open RESQ to check it.',
                icon: '/static/images/resq-logo.png'
            })
        );
    }
});

// Notification click event - handle user interaction
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification clicked:', event.action);
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/notifications';
    
    if (event.action === 'close') {
        return;
    }
    
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then((clientList) => {
            // Check if RESQ is already open
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // If not open, open a new window
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Notification close event - optional analytics
self.addEventListener('notificationclose', (event) => {
    console.log('[Service Worker] Notification closed');
});

// Fetch event - network first strategy
self.addEventListener('fetch', (event) => {
    // Only cache GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    const requestUrl = new URL(event.request.url);

    // Only cache same-origin HTTP/HTTPS requests
    if (requestUrl.protocol !== 'http:' && requestUrl.protocol !== 'https:') {
        return;
    }

    if (requestUrl.origin !== self.location.origin) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone).catch((err) => {
                            console.warn('[Service Worker] Cache put failed:', err, event.request.url);
                        });
                    });
                }
                return response;
            })
            .catch(() => {
                // Return cached version if fetch fails
                return caches.match(event.request)
                    .then((response) => {
                        return response || new Response('Offline - content not available', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

console.log('[Service Worker] Loaded and ready');
