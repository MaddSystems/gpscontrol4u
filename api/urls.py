from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'Marketplace API is running',
        'version': '1.0.0'
    })

app_name = 'api'

urlpatterns = [
    # Basic health check
    path('health/', health_check, name='health'),
]
