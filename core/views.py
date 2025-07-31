"""
Core views for health checks and utilities
"""
from django.http import JsonResponse
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    """Basic health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'Kikapu Backend is running',
            'version': '1.0.0'
        })


class DatabaseHealthView(APIView):
    """Database health check endpoint"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return Response({
                'status': 'healthy',
                'database': 'connected'
            })
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }, status=503)