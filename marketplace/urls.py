from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'marketplace'

# API Router for REST endpoints
router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet)
router.register(r"listings", views.ListingViewSet)
router.register(r"messages", views.MessageViewSet)
router.register(r"favorites", views.FavoriteViewSet)
router.register(r"users", views.UserProfileViewSet)

urlpatterns = [
    # Frontend pages
    path('', views.home_view, name='home'),
    path('categorii/', views.categories_view, name='categories'),
    path('categorii/<slug:category_slug>/', views.category_detail_view, name='category_detail'),
    path('anunturi/', views.listings_view, name='listings'),
    path('anunt/<int:listing_id>/', views.listing_detail_view, name='listing_detail'),
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

    # API endpoints (keeping existing structure)
    path("api/", include(router.urls)),
]
