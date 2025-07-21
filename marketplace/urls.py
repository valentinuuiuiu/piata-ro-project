from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from . import views
from .deepseek_chat_refactored import deepseek_chat_view
# Legacy auth views - now redirected to Allauth
from .recommendations import urls as recommendation_urls
from .views.location_api import location_search_api, reverse_geocode_api, geocode_api
from .views.location_picker import location_picker_view, location_picker_modal
from .views.static_views import serve_static_file

app_name = 'marketplace'

# API Router for REST endpoints
router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename='category')
router.register(r"listings", views.ListingViewSet, basename='listing')
router.register(r"messages", views.MessageViewSet, basename='message')
router.register(r"favorites", views.FavoriteViewSet, basename='favorite')
router.register(r"users", views.UserProfileViewSet, basename='userprofile')

urlpatterns = [
    # Recommendation endpoints
    path('recommendations/', include(recommendation_urls)),
    
    # AI Search endpoints
    path('ai/', include('marketplace.ai_search.urls')),
    
    # Verification endpoints
    path('verification/', include('marketplace.verification.urls')),
    
    # Payment endpoints  
    path('payments/', include('marketplace.payments.urls')),
    
    # Legacy authentication redirects (redirect old URLs to Allauth)
    # path('auth/clerk/login/', RedirectView.as_view(url='/accounts/login/', permanent=True), name='legacy_login'),
    # path('auth/clerk/signup/', RedirectView.as_view(url='/accounts/signup/', permanent=True), name='legacy_signup'),
    # path('auth/clerk/logout/', RedirectView.as_view(url='/accounts/logout/', permanent=True), name='legacy_logout'),
    
    # Compatibility URLs for marketplace namespace
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', RedirectView.as_view(url='/accounts/signup/', permanent=True), name='signup'),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=True), name='logout'),

    # Frontend pages
    path('', views.home_view, name='home'),
    path('categorii/', views.category_list, name='categories'),
    path('categorii/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('anunturi/', views.listing_list, name='listings'),
    path('anunt/<slug:slug>/', views.listing_detail, name='listing_detail'),
    path('adauga-anunt/', views.add_listing_view, name='add_listing'),
    path('profil/', views.profile_view, name='profile'),
    path('profil/editare/', views.profile_edit_view, name='profile_edit'),
    path('mesaje/', views.messages_view, name='messages'),
    path('conversatie/<int:user_id>/', views.conversation_view, name='conversation'),
    path('trimite-mesaj/<int:listing_id>/', views.send_message_view, name='send_message'),
    path('favorite/', views.favorites_view, name='favorites'),
    path('favorite/toggle/<int:listing_id>/', views.toggle_favorite_view, name='toggle_favorite'),
    path('telefon/<int:listing_id>/', views.show_phone_view, name='show_phone'),
    path('raportare/<int:listing_id>/', views.report_listing_view, name='report_listing'),
    path('utilizator/<str:username>/', views.public_profile_view, name='public_profile'),
    
    # Credits and Promotion System
    path('credite/', views.credits_dashboard, name='buy_credits'),
    path('credite/plata/', views.process_payment_view, name='process_payment'),
    path('credite/succes/', views.payment_success, name='payment_success'),
    path('promoveaza/<int:listing_id>/', views.promote_listing_view, name='promote_listing'),
    
    # Legal Pages
    path('termeni-si-conditii/', views.terms_of_service_view, name='terms'),
    path('politica-confidentialitate/', views.privacy_policy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),
    path('despre-noi/', views.about_view, name='about'),
    path('ajutor/', views.help_view, name='help'),
    
    # Stripe Webhook
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    
    # Floating Chat
    path('chat/', views.floating_chat_view, name='floating_chat'),
    path('api/deepseek-chat/', deepseek_chat_view, name='deepseek_chat'),

    # API endpoints (keeping existing structure)
    path("api/", include(router.urls)),
    
    # Location API endpoints
    path('api/locations/search/', location_search_api, name='location_search_api'),
    path('api/locations/reverse-geocode/', reverse_geocode_api, name='reverse_geocode_api'),
    path('api/locations/geocode/', geocode_api, name='geocode_api'),
    
    # Location picker
    path('locatie/', location_picker_view, name='location_picker'),
    path('locatie/modal/', location_picker_modal, name='location_picker_modal'),
    
    # Custom static file server
    path('static/css/<path:path>', serve_static_file, {'path': 'css/main.css'}, name='serve_css'),
]
