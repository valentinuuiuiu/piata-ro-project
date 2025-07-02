from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet)
router.register(r"listings", views.ListingViewSet)
router.register(r"messages", views.MessageViewSet)
router.register(r"favorites", views.FavoriteViewSet)
router.register(r"users", views.UserProfileViewSet)

urlpatterns = [
    path("", include(router.urls)),
    # Location-based endpoints
    path("locations/search/", views.search_locations, name="search_locations"),
    path("locations/popular/", views.get_popular_locations, name="popular_locations"),
    path("locations/stats/", views.get_location_stats, name="location_stats"),
    path("locations/analytics/", views.get_location_analytics, name="location_analytics"),
    path("listings/populate-coordinates/", views.populate_listing_coordinates, name="populate_coordinates"),
]
