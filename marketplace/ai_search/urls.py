"""
URL configuration for AI Search
"""

from django.urls import path
from . import views

app_name = 'ai_search'

urlpatterns = [
    # AI Search endpoints
    path('search/', views.ai_search, name='ai_search'),
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('similar-items/', views.get_similar_items, name='get_similar_items'),
    path('trending/', views.get_trending_items, name='get_trending_items'),
    path('price-recommendations/', views.get_price_recommendations, name='get_price_recommendations'),
    path('analyze-images/', views.analyze_listing_images, name='analyze_listing_images'),
    path('search-suggestions/', views.get_search_suggestions, name='get_search_suggestions'),
]
