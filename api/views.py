from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal

from marketplace.models import (
    Category,
    Favorite,
    Listing,
    Message,
    UserProfile,
    Location,
)
from marketplace.location_services import LocationService
from .serializers import (
    CategorySerializer,
    FavoriteCreateSerializer,
    FavoriteSerializer,
    ListingCreateSerializer,
    ListingSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    UserProfileSerializer,
    UserSerializer,
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "sender"):
            return obj.sender == request.user
        return False


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    @action(detail=True, methods=["get"])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = Category.objects.filter(parent=category)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def listings(self, request, pk=None):
        category = self.get_object()
        listings = Listing.objects.filter(
            Q(category=category) | Q(subcategory=category), status="active"
        )
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["created_at", "price", "views"]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Listing.objects.all()

        # Filter by status (default to active)
        status = self.request.query_params.get("status", "active")
        if status != "all":
            queryset = queryset.filter(status=status)

        # Filter by category
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(
                Q(category_id=category_id) | Q(subcategory_id=category_id)
            )

        # Filter by price range
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Filter by location
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by coordinates and radius (for location-based search)
        latitude = self.request.query_params.get("latitude")
        longitude = self.request.query_params.get("longitude")
        radius = self.request.query_params.get("radius", "10")  # Default 10km radius
        
        if latitude and longitude:
            try:
                lat = float(latitude)
                lon = float(longitude)
                radius_km = float(radius)
                
                # Get nearby listings using our Location model method
                nearby_ids = [
                    listing.id for listing in Listing.get_nearby_listings(lat, lon, radius_km)
                ]
                if nearby_ids:
                    queryset = queryset.filter(id__in=nearby_ids)
                else:
                    queryset = queryset.none()  # No results if no nearby listings
                    
            except (ValueError, TypeError):
                pass  # Ignore invalid coordinates

        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ListingCreateSerializer
        return ListingSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.views += 1
        instance.save(update_fields=["views"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        listing = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        favorite, created = Favorite.objects.get_or_create(user=user, listing=listing)

        if created:
            return Response(
                {"detail": "Listing added to favorites"}, status=status.HTTP_201_CREATED
            )
        return Response(
            {"detail": "Listing already in favorites"}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def unfavorite(self, request, pk=None):
        listing = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            favorite = Favorite.objects.get(user=user, listing=listing)
            favorite.delete()
            return Response(
                {"detail": "Listing removed from favorites"}, status=status.HTTP_200_OK
            )
        except Favorite.DoesNotExist:
            return Response(
                {"detail": "Listing not in favorites"}, status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=["get"])
    def nearby(self, request, pk=None):
        """Get nearby listings for a specific listing"""
        listing = self.get_object()
        
        if not listing.has_coordinates:
            return Response(
                {"detail": "Listing does not have coordinates"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        radius = request.query_params.get("radius", "10")
        try:
            radius_km = float(radius)
        except (ValueError, TypeError):
            radius_km = 10.0
        
        nearby_listings = Listing.get_nearby_listings(
            float(listing.latitude), 
            float(listing.longitude), 
            radius_km, 
            exclude_listing=listing
        )
        
        serializer = ListingSerializer(nearby_listings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["post"])
    def geocode(self, request):
        """Geocode an address to get coordinates"""
        address = request.data.get('address', '')
        city = request.data.get('city', '')
        
        if not address and not city:
            return Response(
                {"error": "Address or city is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = LocationService.geocode_address(address, city)
        if result:
            return Response(result)
        else:
            return Response(
                {"error": "Could not geocode the provided address"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=["post"])
    def reverse_geocode(self, request):
        """Reverse geocode coordinates to get address"""
        try:
            latitude = float(request.data.get('latitude'))
            longitude = float(request.data.get('longitude'))
        except (ValueError, TypeError):
            return Response(
                {"error": "Valid latitude and longitude are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = LocationService.reverse_geocode(latitude, longitude)
        if result:
            return Response(result)
        else:
            return Response(
                {"error": "Could not reverse geocode the provided coordinates"},
                status=status.HTTP_404_NOT_FOUND
            )


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MessageCreateSerializer
        return MessageSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FavoriteCreateSerializer
        return FavoriteSerializer


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=["get"])
    def listings(self, request, pk=None):
        user = self.get_object()
        listings = Listing.objects.filter(user=user, status="active")
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)


# Location-based API endpoints
@api_view(['GET'])
def search_locations(request):
    """Search for locations by name"""
    query = request.GET.get('q', '')
    limit = int(request.GET.get('limit', 10))
    
    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    import time
    start_time = time.time()
    
    results = LocationService.search_locations(query, limit)
    
    response_time = time.time() - start_time
    
    # Log search analytics
    try:
        from marketplace.services.location_analytics import LocationAnalytics
        LocationAnalytics.log_location_search(query, len(results), response_time)
    except ImportError:
        pass
    
    return Response({
        'results': results,
        'query': query,
        'count': len(results),
        'response_time': round(response_time, 3)
    })


@api_view(['GET'])
def get_popular_locations(request):
    """Get popular Romanian cities for location selection"""
    cities = []
    for city, coords in LocationService.ROMANIA_CITIES.items():
        cities.append({
            'name': city,
            'latitude': coords[0],
            'longitude': coords[1],
            'type': 'city',
            'formatted_address': f"{city}, România"
        })
    
    return Response({'results': cities})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def populate_listing_coordinates(request):
    """Populate coordinates for listings that don't have them"""
    user = request.user
    updated_count = 0
    
    # Get user's listings without coordinates
    listings = Listing.objects.filter(
        user=user,
        latitude__isnull=True,
        longitude__isnull=True
    )
    
    for listing in listings:
        if LocationService.populate_listing_coordinates(listing):
            updated_count += 1
    
    return Response({
        'message': f'Updated coordinates for {updated_count} listings',
        'updated_count': updated_count
    })


@api_view(['GET'])
def get_location_stats(request):
    """Get statistics about listings by location"""
    from django.db.models import Count
    
    # Get listings count by city
    city_stats = (
        Listing.objects
        .filter(status='active', city__isnull=False)
        .values('city', 'county')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    
    # Get listings count by county
    county_stats = (
        Listing.objects
        .filter(status='active', county__isnull=False)
        .values('county')
        .annotate(count=Count('id'))
        .order_by('-count')[:20]
    )
    
    return Response({
        'cities': list(city_stats),
        'counties': list(county_stats)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_location_analytics(request):
    """Get location service analytics - admin only"""
    if not request.user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        from marketplace.services.location_analytics import LocationAnalytics
        
        period = request.GET.get('period', 'daily')  # daily, weekly
        
        if period == 'weekly':
            stats = LocationAnalytics.get_weekly_stats()
        else:
            date = request.GET.get('date')
            stats = LocationAnalytics.get_daily_stats(date)
        
        health = LocationAnalytics.get_service_health()
        popular = LocationAnalytics.get_popular_locations()
        
        return Response({
            'period': period,
            'stats': stats,
            'health': health,
            'popular_locations': popular
        })
        
    except ImportError:
        return Response({
            'error': 'Analytics not available',
            'stats': {},
            'health': {'status': 'unknown'},
            'popular_locations': []
        })
