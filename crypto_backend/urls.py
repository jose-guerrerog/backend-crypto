from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy', 'message': 'Django backend is running!'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('portfolio.urls')),  
    path('health/', health_check)
]