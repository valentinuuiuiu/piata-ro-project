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
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.contrib.admin import views as admin_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView

from piata_ro.views import (
    process_mcp_query, test_endpoint, home, interact_with_mcp_agents, 
    natural_language_query, openai_models_endpoint, openai_chat_completions
)
from marketplace.admin import admin_site

urlpatterns = [
    # Health checks for monitoring and Azure deployment
    path('health/', include('piata_ro.health_urls')),
    
    path('', include(('marketplace.urls', 'marketplace'), namespace='marketplace')),  # Include marketplace URLs for frontend
    path('ai/', include(('ai_assistant.urls', 'ai_assistant'), namespace='ai_assistant')),  # Add AI assistant URLs
    path('ai-assistant/', include(('ai_assistant.urls', 'ai_assistant'), namespace='ai_assistant_alt')),  # Alternative path
    path('admin/', admin_site.urls),
    
    # Admin password reset URLs
    path('admin/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='admin/password_reset_form.html',
        email_template_name='admin/password_reset_email.html',
        subject_template_name='admin/password_reset_subject.txt',
        success_url='/admin/password_reset/done/',
    ), name='admin_password_reset'),
    path('admin/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='admin/password_reset_done.html'
    ), name='admin_password_reset_done'),
    path('admin/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='admin/password_reset_confirm.html',
        success_url='/admin/reset/done/',
    ), name='admin_password_reset_confirm'),
    path('admin/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='admin/password_reset_complete.html'
    ), name='admin_password_reset_complete'),
    
    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    
    # Allauth URLs (includes social auth)
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', CreateView.as_view(
        template_name='registration/register.html',
        form_class=UserCreationForm,
        success_url='/accounts/login/'
    ), name='register'),
    path('accounts/social/', include('allauth.urls')),
    
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

# Add media and static serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
