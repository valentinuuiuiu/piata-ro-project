from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from . import views
from .deepseek_chat_refactored import deepseek_chat_view
# from .views.auth import login_view, verify_mfa # Old auth views
from marketplace.views import auth as marketplace_auth_views # New auth views
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
    # Recommendation endpoints
    path('recommendations/', include(recommendation_urls)),
    
    # Verification endpoints
    path('verification/', include('marketplace.verification.urls')),
    
    # Payment endpoints  
    path('payments/', include('marketplace.payments.urls')),
    
    # Authentication - To be replaced by Clerk
    # path('login/', login_view, name='login'),
    # path('login/mfa/', verify_mfa, name='verify_mfa'),
    # path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password Reset - To be replaced by Clerk
    # path('password_reset/', PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    # path('password_reset/done/', PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    # path('reset/done/', PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # New Clerk Authentication URLs
    path('auth/clerk/login/', marketplace_auth_views.clerk_login_redirect_view, name='clerk_login'),
    path('auth/clerk/signup/', marketplace_auth_views.clerk_signup_redirect_view, name='clerk_signup'),
    path('auth/clerk/logout/', marketplace_auth_views.clerk_logout_view, name='clerk_logout'),
    path('auth/clerk/callback/', marketplace_auth_views.clerk_callback_view, name='clerk_callback'),

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
