import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from portfolio.consumers import CryptoPriceConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/prices/", CryptoPriceConsumer.as_asgi()),
        ])
    ),
})