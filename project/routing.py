"""
WebSocket URL routing for real-time dashboard updates and driver notifications
"""
from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from . import consumers
from .jwt_auth_middleware import JWTAuthMiddlewareStack

websocket_urlpatterns = [
    # Dashboard يستخدم session authentication
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    # Driver يستخدم JWT authentication
    re_path(r'ws/driver/$', consumers.DriverConsumer.as_asgi()),

    # //
    # Per-order tracking channel
    re_path(r'ws/order/(?P<order_id>\d+)/$', consumers.OrderTrackingConsumer.as_asgi()),
]
