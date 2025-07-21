"""
Health check URLs
"""

from django.urls import path
from . import health

urlpatterns = [
    path('', health.health_check, name='health_check'),
    path('ready/', health.ready_check, name='ready_check'),
    path('live/', health.live_check, name='live_check'),
]
