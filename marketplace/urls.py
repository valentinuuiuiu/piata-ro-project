from django.urls import include, path
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from rest_framework.routers import DefaultRouter

from . import views
from .deepseek_chat_refactored import deepseek_chat_view
from .recommendations import urls as recommendation_urls

app_name = 'marketplace'

# API Router for REST endpoints
router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename='category')
router.register(r"listings", views.ListingViewSet, basename='listing')
router.register(r"messages", views.MessageViewSet, basename='message')
router.register(r"favorites", views.FavoriteViewSet, basename='favorite')
router.register(r"users", views.UserProfileViewSet, basename='userprofile')

urlpatterns = [
    # Authentication views
    path('auth/clerk/login/', views.login_view, name='login'),
    path('auth/clerk/signup/', views.signup_view, name='signup'),
    path('auth/clerk/mfa/', views.verify_mfa, name='verify_mfa'),
    path('auth/clerk/logout/', LogoutView.as_view(), name='logout'),
    path('auth/clerk/password_reset/', PasswordResetView.as_view(template_name='account/password_reset.html'), name='password_reset'),
    path('auth/clerk/password_reset/done/', PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('auth/clerk/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('auth/clerk/reset/done/', PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    
    # Recommendation endpoints
    path('recommendations/', include(recommendation_urls)),
    
    # Verification endpoints
    path('verification/', include('marketplace.verification.urls')),
    
    # Payment endpoints  
    path('payments/', include('marketplace.payments.urls')),
    
    # Frontend pages
    path('', views.home_view, name='home'),
    path('categorii/', views.category_list, name='categories'),
    path('categorii/<slug:category_slug>/', views.category_detail, name='category_detail'),
    path('anunturi/', views.listing_list, name='listings'),
    path('cautare/', views.search, name='search'),
    path('anunt/<slug:slug>/', views.listing_detail, name='listing_detail'),
    path('adauga-anunt/', views.add_listing_view, name='add_listing'),
    path('profil/', views.profile_view, name='profile'),
    path('profil/editare/', views.profile_edit_view, name='profile_edit'),
    path('mesaje/', views.messages_view, name='messages'),
    path('conversatie/<int:user_id>/', views.conversation_view, name='conversation'),
    path('trimite-mesaj/<int:listing_id>/', views.send_message_view, name='send_message'),
    path('favorite/', views.favorites_view, name='favorites'),
    path('favorite/toggle/<int:listing_id>/', views.toggle_favorite_view, name='toggle_favorite'),
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
]
