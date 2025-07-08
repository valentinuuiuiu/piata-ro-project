


from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('recommendations/<int:user_id>/', views.user_recommendations, name='user-recommendations'),
    path('similar/<int:listing_id>/', views.similar_listings, name='similar-listings'),
]


