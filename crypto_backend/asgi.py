import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_backend.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import AFTER get_asgi_application()
from portfolio.consumers import PriceConsumer

# Custom middleware to handle CORS for WebSockets
class CorsMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Allow WebSocket connections from your frontend
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode()
            
            allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ]
            
            if origin in allowed_origins or not origin:  # Allow empty origin for testing
                return await self.inner(scope, receive, send)
            else:
                # Reject the connection
                await send({"type": "websocket.close", "code": 4003})
                return
        
        return await self.inner(scope, receive, send)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": CorsMiddleware(
        AuthMiddlewareStack(
            URLRouter([
                path("ws/prices/", PriceConsumer.as_asgi()),
            ])
        )
    ),
})