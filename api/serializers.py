from django.contrib.auth.models import User
from rest_framework import serializers

from marketplace.models import Category, Favorite, Listing, Message, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ["user", "avatar", "bio", "phone", "location", "is_premium"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon", "color", "parent"]


class ListingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = CategorySerializer(read_only=True)
    distance = serializers.SerializerMethodField()
    full_address = serializers.ReadOnlyField()
    has_coordinates = serializers.ReadOnlyField()
    main_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "price",
            "currency",
            "location",
            "latitude",
            "longitude",
            "address",
            "city",
            "county",
            "postal_code",
            "country",
            "location_verified",
            "full_address",
            "has_coordinates",
            "distance",
            "images",
            "main_image",
            "category_name",
            "user",
            "category",
            "subcategory",
            "status",
            "created_at",
            "updated_at",
            "expires_at",
            "is_premium",
            "views",
            "metadata",
            "is_verified",
        ]
        read_only_fields = [
            "user", 
            "views", 
            "is_verified", 
            "created_at", 
            "updated_at", 
            "location_verified",
            "full_address",
            "has_coordinates",
            "distance"
        ]
    
    def get_distance(self, obj):
        """Calculate distance from a reference point if provided in context"""
        request = self.context.get('request')
        if not request:
            return None
            
        ref_lat = request.query_params.get('ref_latitude')
        ref_lon = request.query_params.get('ref_longitude')
        
        if ref_lat and ref_lon and obj.has_coordinates:
            try:
                distance = obj.distance_to_point(float(ref_lat), float(ref_lon))
                return round(distance, 2) if distance else None
            except (ValueError, TypeError):
                return None
        return None
    
    def get_main_image(self, obj):
        """Get the main image URL for the listing"""
        main_image = obj.main_image
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None


class ListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = [
            "title",
            "description",
            "price",
            "currency",
            "location",
            "latitude",
            "longitude", 
            "address",
            "city",
            "county",
            "postal_code",
            "country",
            "images",
            "category",
            "subcategory",
        ]

    def create(self, validated_data):
        from marketplace.location_services import LocationService
        
        validated_data["user"] = self.context["request"].user
        listing = super().create(validated_data)
        
        # Try to populate coordinates if not provided
        if not listing.latitude or not listing.longitude:
            LocationService.populate_listing_coordinates(listing)
        
        return listing
    
    def update(self, instance, validated_data):
        from marketplace.location_services import LocationService
        
        # Check if location-related fields have changed
        location_fields = ['location', 'address', 'city', 'county', 'postal_code']
        location_changed = any(field in validated_data for field in location_fields)
        
        # Update the instance
        updated_instance = super().update(instance, validated_data)
        
        # If location changed and no coordinates provided, try to geocode
        if location_changed and (not validated_data.get('latitude') or not validated_data.get('longitude')):
            LocationService.populate_listing_coordinates(updated_instance)
        
        return updated_instance


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "receiver",
            "listing",
            "content",
            "created_at",
            "is_read",
        ]
        read_only_fields = ["sender", "created_at"]


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["receiver", "listing", "content"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "user", "listing", "created_at"]
        read_only_fields = ["user", "created_at"]


class FavoriteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["listing"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
