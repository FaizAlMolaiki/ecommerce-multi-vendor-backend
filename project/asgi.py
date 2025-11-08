"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# ===== إضافة JWT Authentication للموصل - بداية التعديل =====
# استيراد JWT middleware بعد تهيئة Django
from .jwt_auth_middleware import JWTAuthMiddlewareStack
# ===== إضافة JWT Authentication للموصل - نهاية التعديل =====

# Now we can import routing and consumers
import project.routing
from project import consumers

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter([
        # Dashboard مع session authentication
        re_path(r'ws/dashboard/$', AuthMiddlewareStack(consumers.DashboardConsumer.as_asgi())),
        # Driver مع JWT authentication
        re_path(r'ws/driver/$', JWTAuthMiddlewareStack(consumers.DriverConsumer.as_asgi())),
        re_path(r'ws/order/(?P<order_id>\d+)/$',AuthMiddlewareStack(consumers.OrderTrackingConsumer.as_asgi())),

    ]),
})
