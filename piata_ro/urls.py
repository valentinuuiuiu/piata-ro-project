"""
URL configuration for piata_ro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView
import os

from piata_ro.views import (
    process_mcp_query, test_endpoint, home, interact_with_mcp_agents, 
    natural_language_query, openai_models_endpoint, openai_chat_completions
)
from piata_ro.health_checks import (
    health_check, readiness_check, liveness_check, 
    mcp_health_check, database_metrics, cache_metrics
)
from django.contrib import admin

urlpatterns = [
    path('', include(('marketplace.urls', 'marketplace'), namespace='marketplace')),  # Include marketplace URLs for frontend
    path('blog/', include(('marketplace.urls_blog', 'blog'), namespace='blog')),  # Blog URLs
    path('ai/', include(('ai_assistant.urls', 'ai_assistant'), namespace='ai_assistant')),  # Add AI assistant URLs
    path('ai-assistant/', include(('ai_assistant.urls', 'ai_assistant'), namespace='ai_assistant_alt')),  # Alternative path
    path('admin/', admin.site.urls),
    
    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    
    # Explicit password reset confirm URL
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('auth/', include('django.contrib.auth.urls')),  # Add default auth routes
    # Allauth URLs (includes social auth)
    path('accounts/', include('allauth.urls')),
    
    # OpenAI API compatibility endpoints
    path('v1/models', openai_models_endpoint, name='openai_models'),
    path('v1/chat/completions', openai_chat_completions, name='openai_chat'),
    
    path('api/', include('api.urls')),
    path('api/query/', natural_language_query, name='natural_language_query'),
    path('mcp/process/', process_mcp_query, name='mcp_processor'),
    path('mcp/agents/', interact_with_mcp_agents, name='mcp_agents'),
    path('test_endpoint/', test_endpoint, name='test_endpoint'),
    path('legacy/', home, name='legacy_home'),  # Keep old home as legacy
    
    # Health check and monitoring endpoints
    path('health/', health_check, name='health_check'),
    path('health/readiness/', readiness_check, name='readiness_check'),
    path('health/liveness/', liveness_check, name='liveness_check'),
    path('health/mcp/<int:port>/', mcp_health_check, name='mcp_health_check'),
    path('health/database/metrics/', database_metrics, name='database_metrics'),
    path('health/cache/metrics/', cache_metrics, name='cache_metrics'),
]

# Add media and static serving in development
if settings.DEBUG:
    print(f"DEBUG: Adding static files serving for {settings.STATIC_URL} from {settings.STATIC_ROOT}")
    print(f"DEBUG: Static root exists: {os.path.exists(settings.STATIC_ROOT)}")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
