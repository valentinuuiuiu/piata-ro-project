


from django.urls import path
from .views import *
from . import dispute_views

urlpatterns = [
    path('escrow/create/<int:listing_id>/', views.create_escrow, name='create-escrow'),
    path('escrow/release/<int:escrow_id>/', views.release_escrow, name='release-escrow'),
    path('escrow/refund/<int:escrow_id>/', views.refund_escrow, name='refund-escrow'),
    path('dispute/open/<int:escrow_id>/', dispute_views.open_dispute, name='open-dispute'),
    path('dispute/resolve/<int:escrow_id>/', dispute_views.resolve_dispute, name='resolve-dispute'),
]


