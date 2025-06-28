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

from piata_ro.views import (
    process_mcp_query, test_endpoint, home, interact_with_mcp_agents, 
    natural_language_query, openai_models_endpoint, openai_chat_completions
)
from marketplace.views import register_view

urlpatterns = [
    path('', include(('marketplace.urls', 'marketplace'), namespace='marketplace')),  # Include marketplace URLs for frontend
    path('ai/', include(('ai_assistant.urls', 'ai_assistant'), namespace='ai_assistant')),  # Add AI assistant URLs
    path('admin/', admin.site.urls),
    
    # Allauth URLs (includes social auth)
    path('accounts/', include('allauth.urls')),
    
    # Keep custom register view
    path('register/', register_view, name='register'),
    
    # OpenAI API compatibility endpoints
    path('v1/models', openai_models_endpoint, name='openai_models'),
    path('v1/chat/completions', openai_chat_completions, name='openai_chat'),
    
    path('api/', include('api.urls')),
    path('api/query/', natural_language_query, name='natural_language_query'),
    path('mcp/process/', process_mcp_query, name='mcp_processor'),
    path('mcp/agents/', interact_with_mcp_agents, name='mcp_agents'),
    path('test_endpoint/', test_endpoint, name='test_endpoint'),
    path('legacy/', home, name='legacy_home'),  # Keep old home as legacy
]

# Add media serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
