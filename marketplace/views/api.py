from rest_framework import viewsets
from ..models import Category, Listing, Message, Favorite, UserProfile
from ..serializers import (
    CategorySerializer,
    ListingSerializer,
    MessageSerializer,
    FavoriteSerializer,
    UserProfileSerializer,
    ListingCreateSerializer,
    MessageCreateSerializer,
    FavoriteCreateSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status='active')
    filterset_fields = ['category', 'user', 'is_featured']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ListingCreateSerializer
        return ListingSerializer

class MessageViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'listing')
        
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MessageCreateSerializer
        return MessageSerializer

class FavoriteViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('listing')
        
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FavoriteCreateSerializer
        return FavoriteSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
