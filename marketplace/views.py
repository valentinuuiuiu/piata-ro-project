from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
# Note: stripe will be installed separately
try:
    import stripe
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None

from .models import Category, Favorite, Listing, Message, UserProfile, ListingImage, CreditPackage, Payment, CreditTransaction, ListingBoost, ListingReport #, PromoteListingForm
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
from .forms import ListingForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm, PromoteListingForm

# Configure Stripe
if stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY

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


def home(request):
    """Homepage view."""
    # Get all categories for the dropdown
    categories = Category.objects.all()

    # Get featured/promoted listings
    featured_listings = Listing.objects.filter(
        status="active", is_featured=True
    ).order_by("-created_at")[:8]

    # Get recent listings
    recent_listings = Listing.objects.filter(status="active").order_by("-created_at")[
        :8
    ]

    context = {
        "categories": categories,
        "featured_listings": featured_listings,
        "recent_listings": recent_listings,
    }

    return render(request, "marketplace/index.html", context)


# Frontend Views for the Comprehensive Marketplace

def home_view(request):
    """Homepage view with enhanced functionality."""
    # Get all categories for the dropdown
    categories = Category.objects.all()

    # Get featured/promoted listings
    featured_listings = Listing.objects.filter(
        status="active", is_featured=True
    ).order_by("-created_at")[:8]

    # Get recent listings
    recent_listings = Listing.objects.filter(status="active").order_by("-created_at")[:12]

    # Get statistics
    total_listings = Listing.objects.filter(status="active").count()
    total_categories = Category.objects.count()

    context = {
        "categories": categories,
        "featured_listings": featured_listings,
        "recent_listings": recent_listings,
        "total_listings": total_listings,
        "total_categories": total_categories,
    }

    return render(request, "marketplace/index.html", context)


def categories_view(request):
    """Categories listing page."""
    categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    
    context = {
        "categories": categories,
        "page_title": "Toate categoriile",
    }
    
    return render(request, "marketplace/categories.html", context)


def category_detail_view(request, category_slug):
    """Category detail page with listings."""
    from django.shortcuts import get_object_or_404
    
    category = get_object_or_404(Category, slug=category_slug)
    
    # Get subcategories
    subcategories = Category.objects.filter(parent=category)
    
    # Get listings in this category and subcategories
    category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
    listings = Listing.objects.filter(
        category_id__in=category_ids,
        status="active"
    ).order_by("-created_at")
    
    # Handle pagination
    from django.core.paginator import Paginator
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        "category": category,
        "subcategories": subcategories,
        "listings": page_obj,
        "page_title": f"Categoria: {category.name}",
    }
    
    return render(request, "marketplace/category_detail.html", context)


def listings_view(request):
    """All listings page with filtering."""
    listings = Listing.objects.filter(status="active").order_by("-created_at")
    categories = Category.objects.all()
    
    # Apply filters
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')
    
    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_id:
        listings = listings.filter(category_id=category_id)
    
    if min_price:
        try:
            listings = listings.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            listings = listings.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    if location:
        listings = listings.filter(location__icontains=location)
    
    # Handle pagination
    from django.core.paginator import Paginator
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        "listings": page_obj,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "location": location,
        "page_title": "Toate anunțurile",
    }
    
    return render(request, "marketplace/listings.html", context)


def listing_detail_view(request, listing_id):
    """Listing detail page."""
    from django.shortcuts import get_object_or_404
    
    listing = get_object_or_404(Listing, id=listing_id, status="active")
    
    # Increment views
    listing.views += 1
    listing.save(update_fields=['views'])
    
    # Get related listings
    related_listings = Listing.objects.filter(
        category=listing.category,
        status="active"
    ).exclude(id=listing.id)[:6]
    
    context = {
        "listing": listing,
        "related_listings": related_listings,
        "page_title": listing.title,
    }
    
    return render(request, "marketplace/listing_detail.html", context)


def add_listing_view(request):
    """Add new listing page."""
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.status = 'active'  # Set to active by default
            listing.save()
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ListingImage.objects.create(
                    listing=listing,
                    image=image,
                    is_main=(i == 0)  # First image is main
                )
            
            messages.success(request, 'Anunțul a fost creat cu succes!')
            return redirect('marketplace:listing_detail', listing_id=listing.id)
        else:
            messages.error(request, 'Te rugăm să corectezi erorile de mai jos.')
    else:
        form = ListingForm()
    
    categories = Category.objects.filter(parent__isnull=True)
    
    context = {
        "form": form,
        "categories": categories,
        "page_title": "Adaugă anunț nou",
    }
    
    return render(request, "marketplace/add_listing.html", context)


def profile_view(request):
    """User profile page."""
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_listings = Listing.objects.filter(user=request.user).order_by("-created_at")
    
    context = {
        "user_listings": user_listings,
        "page_title": "Profilul meu",
    }
    
    return render(request, "marketplace/profile.html", context)


@login_required
def profile_edit_view(request):
    """Profile edit page."""
    user_form = UserUpdateForm(instance=request.user)
    profile_form = UserProfileForm(instance=request.user.profile)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profilul tău a fost actualizat cu succes!')
            return redirect('marketplace:profile')
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': 'Editează profilul',
    }
    
    return render(request, "marketplace/profile_edit.html", context)


def messages_view(request):
    """Messages page with conversation grouping."""
    from django.shortcuts import redirect
    from django.db.models import Q, Max, Count
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get conversations - group messages by participants
    conversations = []
    
    # Get all unique conversation partners
    conversation_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | 
        Q(received_messages__sender=request.user)
    ).distinct().exclude(id=request.user.id)
    
    for other_user in conversation_users:
        # Get latest message in this conversation
        latest_message = Message.objects.filter(
            (Q(sender=request.user, receiver=other_user) | 
             Q(sender=other_user, receiver=request.user))
        ).order_by('-created_at').first()
        
        # Count unread messages from this user
        unread_count = Message.objects.filter(
            sender=other_user, 
            receiver=request.user, 
            is_read=False
        ).count()
        
        if latest_message:
            conversations.append({
                'other_user': other_user,
                'last_message': latest_message,
                'unread_count': unread_count,
            })
    
    # Sort conversations by latest message
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)
    
    context = {
        "conversations": conversations,
        "page_title": "Mesajele mele",
    }
    
    return render(request, "marketplace/messages.html", context)


@login_required
def conversation_view(request, user_id):
    """View a conversation with a specific user."""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    from django.db.models import Q
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Get all messages between these two users
    messages = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) | 
         Q(sender=other_user, receiver=request.user))
    ).order_by('created_at')
    
    # Mark messages as read
    Message.objects.filter(
        sender=other_user, 
        receiver=request.user, 
        is_read=False
    ).update(is_read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'created_at': message.created_at.strftime('%H:%M'),
                        'sender': message.sender.username
                    }
                })
            return redirect('marketplace:conversation', user_id=user_id)
    
    context = {
        'other_user': other_user,
        'messages': messages,
        'page_title': f'Conversație cu {other_user.username}',
    }
    
    return render(request, "marketplace/conversation.html", context)


@login_required
def send_message_view(request, listing_id):
    """Send a message about a specific listing."""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    listing = get_object_or_404(Listing, id=listing_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content and listing.user != request.user:
            message = Message.objects.create(
                sender=request.user,
                receiver=listing.user,
                listing=listing,
                content=content
            )
            messages.success(request, 'Mesajul tău a fost trimis cu succes!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
                
            return redirect('marketplace:listing_detail', listing_id=listing_id)
    
    return redirect('marketplace:listing_detail', listing_id=listing_id)


def favorites_view(request):
    """Favorites page."""
    from django.shortcuts import redirect
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    favorites = Favorite.objects.filter(user=request.user).select_related('listing')
    
    context = {
        "favorites": favorites,
        "page_title": "Favoritele mele",
    }
    
    return render(request, "marketplace/favorites.html", context)


@login_required
def toggle_favorite_view(request, listing_id):
    """Toggle favorite status for a listing."""
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    if request.method == 'POST':
        listing = get_object_or_404(Listing, id=listing_id)
        
        # Check if already favorited
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if not created:
            # Already favorited, so remove it
            favorite.delete()
            is_favorited = False
            message = "Anunțul a fost eliminat din favorite"
        else:
            is_favorited = True
            message = "Anunțul a fost adăugat la favorite"
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_favorited': is_favorited,
                'message': message
            })
        
        messages.success(request, message)
        return redirect('marketplace:listing_detail', listing_id=listing_id)
    
    return JsonResponse({'success': False})


def search_view(request):
    """Enhanced search results page with advanced filtering including location-based distance."""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-created_at')
    enable_distance = request.GET.get('enable_distance', False)
    distance = request.GET.get('distance', '10')
    user_lat = request.GET.get('user_lat', '')
    user_lng = request.GET.get('user_lng', '')
    date_from = request.GET.get('date_from', '')
    condition = request.GET.get('condition', '')
    
    categories = Category.objects.all()
    listings = Listing.objects.filter(status="active")
    
    # Apply search query
    if query:
        listings = listings.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(city__icontains=query) |
            Q(address__icontains=query)
        )
    
    # Apply category filter
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            # Include subcategories
            category_ids = [category.id]
            subcategories = Category.objects.filter(parent=category)
            category_ids.extend(subcategories.values_list('id', flat=True))
            listings = listings.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            pass
    
    # Apply price filters
    if min_price:
        try:
            listings = listings.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            listings = listings.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply date filter
    if date_from:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            listings = listings.filter(created_at__date__gte=date_obj)
        except ValueError:
            pass
    
    # Apply condition filter (if you have a condition field on your model)
    # if condition:
    #     listings = listings.filter(condition=condition)
    
    # Apply location filter
    if location and not enable_distance:
        # Simple text-based location filter
        listings = listings.filter(
            Q(location__icontains=location) |
            Q(city__icontains=location) |
            Q(county__icontains=location)
        )
    
    # Apply distance-based filtering
    if enable_distance and user_lat and user_lng:
        try:
            from .models import Location
            user_latitude = float(user_lat)
            user_longitude = float(user_lng)
            distance_km = float(distance)
            
            # Filter listings within the specified distance
            nearby_listings = []
            for listing in listings:
                if listing.latitude and listing.longitude:
                    distance_to_listing = Location.calculate_distance(
                        user_latitude, user_longitude,
                        float(listing.latitude), float(listing.longitude)
                    )
                    if distance_to_listing <= distance_km:
                        # Add distance as an attribute for sorting/display
                        listing._distance = distance_to_listing
                        nearby_listings.append(listing)
            
            # Convert back to queryset with proper IDs
            if nearby_listings:
                listing_ids = [listing.id for listing in nearby_listings]
                listings = Listing.objects.filter(id__in=listing_ids, status="active")
                
                # Store distance data for later use
                distance_map = {listing.id: listing._distance for listing in nearby_listings}
                request._distance_map = distance_map
            else:
                listings = Listing.objects.none()
        
        except (ValueError, TypeError):
            pass
    
    # Apply sorting
    if sort_by == 'price':
        listings = listings.order_by('price')
    elif sort_by == '-price':
        listings = listings.order_by('-price')
    elif sort_by == 'created_at':
        listings = listings.order_by('created_at')
    elif sort_by == 'title':
        listings = listings.order_by('title')
    elif sort_by == 'distance' and enable_distance and user_lat and user_lng:
        # Sort by distance (if we have distance data)
        if hasattr(request, '_distance_map'):
            listings = list(listings)
            listings.sort(key=lambda x: request._distance_map.get(x.id, float('inf')))
    else:  # -created_at (default)
        listings = listings.order_by('-created_at')
    
    # Handle pagination
    from django.core.paginator import Paginator
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add distance information to listings for display
    if hasattr(request, '_distance_map'):
        for listing in page_obj:
            distance_km = request._distance_map.get(listing.id)
            if distance_km is not None:
                listing.distance_km = round(distance_km, 1)
    
    context = {
        "results": page_obj,
        "query": query,
        "categories": categories,
        "selected_category": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "location": location,
        "sort_by": sort_by,
        "enable_distance": enable_distance,
        "distance": distance,
        "user_lat": user_lat,
        "user_lng": user_lng,
        "date_from": date_from,
        "condition": condition,
        "total_results": len(listings) if hasattr(request, '_distance_map') else listings.count(),
        "page_title": f"Căutare: {query}" if query else "Căutare",
    }
    
    return render(request, "marketplace/search.html", context)


def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul pentru {username} a fost creat cu succes!')
            login(request, user)
            return redirect('marketplace:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def credits_dashboard(request):
    """Credits dashboard showing balance and purchase options"""
    user_profile = request.user.profile
    credit_packages = CreditPackage.objects.filter(is_active=True).order_by('credits')
    recent_transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'credit_packages': credit_packages,
        'recent_transactions': recent_transactions,
        'promotion_cost': Decimal('0.50'),  # Cost to promote a listing
    }
    return render(request, 'marketplace/credits_cart.html', context)

# @login_required
# def buy_credits(request, package_id):
#     """Handle credit purchase via Stripe (Likely deprecated - uses PaymentIntent, current flow uses Checkout Session)"""
#     try:
#         package = CreditPackage.objects.get(id=package_id, is_active=True)
#         user_profile = request.user.profile
        
#         if request.method == 'POST':
#             try:
#                 # Create Stripe payment intent
#                 intent = stripe.PaymentIntent.create(
#                     amount=int(package.price_eur * 100),  # Stripe expects cents
#                     currency='eur',
#                     metadata={
#                         'user_id': request.user.id,
#                         'package_id': package.id,
#                         'credits': str(package.credits),
#                     }
#                 )
                
#                 # Create payment record
#                 payment = Payment.objects.create(
#                     user=request.user,
#                     amount=package.price_eur,
#                     payment_method='stripe', # This field might not exist on Payment model or needs adjustment
#                     stripe_payment_intent_id=intent.id,
#                     status='pending'
#                 )
                
#                 return JsonResponse({
#                     'client_secret': intent.client_secret,
#                     'payment_id': payment.id
#                 })
                
#             except stripe.error.StripeError as e:
#                 return JsonResponse({'error': str(e)}, status=400)
                
#         context = {
#             'package': package,
#             'user_profile': user_profile,
#             'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
#         }
#         return render(request, 'marketplace/buy_credits.html', context) # This template might also be unused
        
#     except CreditPackage.DoesNotExist:
#         messages.error(request, "Pachetul de credite nu există.")
#         return redirect('marketplace:buy_credits') # Assuming 'credits_dashboard' is 'marketplace:buy_credits'

@login_required
def payment_success(request):
    """Handle successful payment and add credits to user"""
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            import stripe
            from django.conf import settings
            import json
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                # Get metadata from session
                user_id = session.metadata.get('user_id')
                total_credits = int(session.metadata.get('total_credits', 0))
                cart_data = json.loads(session.metadata.get('cart_data', '[]'))
                currency = session.metadata.get('currency', 'ron')
                
                # Verify user
                if str(request.user.id) != user_id:
                    messages.error(request, "Sesiunea de plată nu corespunde cu utilizatorul curent.")
                    return redirect('marketplace:buy_credits')
                
                # Add credits to user profile
                user_profile = request.user.profile
                user_profile.credits_balance += Decimal(str(total_credits)) # Use Decimal for precision
                user_profile.save()
                
                # Create transaction records for each item in cart
                for item in cart_data:
                    credits = item['credits']
                    quantity = item['quantity']
                    price = item['priceEur'] if currency == 'eur' else item['priceRon']
                    
                    for i in range(quantity):
                        CreditTransaction.objects.create(
                            user=request.user,
                            transaction_type='purchase',
                            amount=credits,
                            description=f"Achiziție {credits} credite ({price} {currency.upper()})",
                            reference=session_id
                        )
                
                messages.success(request, f"🎉 Felicitări! Ai primit {total_credits} credite în cont. Plata a fost procesată cu succes!")
                return render(request, 'marketplace/payment_success.html', {
                    'total_credits': total_credits,
                    'session_id': session_id,
                    'cart_data': cart_data,
                    'currency': currency.upper()
                })
                
        except Exception as e:
            messages.error(request, f"A apărut o eroare la procesarea plății: {str(e)}")
    
    messages.error(request, "Sesiunea de plată nu a fost găsită sau este invalidă.")
    return redirect('marketplace:buy_credits')

# This version seems less complete and uses fields not on Listing model (is_promoted, promoted_until)
# The version below (originally named promote_listing_view) is more aligned with the models and form.
# @login_required
# def promote_listing(request, listing_id):
#     """Promote a listing to first page for 0.5 credits"""
#     try:
#         listing = Listing.objects.get(id=listing_id, user=request.user)
#         user_profile = request.user.profile
#         promotion_cost = Decimal('0.50')
        
#         if request.method == 'POST':
#             if user_profile.can_promote_listing(): # can_promote_listing might need adjustment if cost varies
#                 # Deduct credits
#                 if user_profile.deduct_credits(promotion_cost):
#                     # Create listing boost
#                     boost = ListingBoost.objects.create(
#                         listing=listing,
#                         # user=request.user, # ListingBoost model does not have a direct user link, it's via listing.user
#                         boost_type='featured',
#                         credits_cost=int(promotion_cost * 2), # Assumes 0.5 credits = 1 unit in credits_cost if it's integer
#                         duration_days=7, # Hardcoded duration
#                         # expires_at=timezone.now() + timezone.timedelta(days=7)  # ListingBoost calculates this on save
#                     )
                    
#                     # Mark listing as featured
#                     listing.is_featured = True
#                     listing.save()
                    
#                     # Create transaction record
#                     CreditTransaction.objects.create(
#                         user=request.user,
#                         transaction_type='spent', # More generic 'spent'
#                         amount=promotion_cost, # Amount in credits
#                         description=f"Promovare anunț: {listing.title}",
#                         listing=listing
#                     )
                    
#                     messages.success(request, f"Anunțul '{listing.title}' a fost promovat cu succes! Va apărea pe prima pagină timp de 7 zile.")
#                     # Assuming listing_detail takes listing_id, not slug, based on other views.
#                     return JsonResponse({'success': True, 'redirect_url': reverse('marketplace:listing_detail', kwargs={'listing_id': listing.id})})
#                 else:
#                     return JsonResponse({'error': 'Eroare la procesarea creditelor.'}, status=400)
#             else:
#                 return JsonResponse({'error': f'Nu ai suficiente credite. Ai nevoie de {promotion_cost} credite.'}, status=400)
        
#         context = {
#             'listing': listing,
#             'promotion_cost': promotion_cost,
#             'user_credits': user_profile.credits_balance
#         }
#         # This render seems to be for a different promote_listing.html than the form based one.
#         return render(request, 'marketplace/promote_listing.html', context)
        
#     except Listing.DoesNotExist:
#         messages.error(request, "Anunțul nu există sau nu îți aparține.")
#         return redirect('marketplace:profile') # Corrected redirect

@login_required
def credits_history(request):
    """View credit transaction history"""
    transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'transactions': transactions,
        'user_profile': request.user.profile
    }
    return render(request, 'marketplace/credits_history.html', context)


@login_required
def process_payment_view(request):
    """Process Stripe payment for credits from shopping cart."""
    if request.method == 'POST':
        import json
        import stripe
        from django.conf import settings
        
        try:
            # Get cart data from the form
            cart_data = json.loads(request.POST.get('cart_data', '[]'))
            currency = request.POST.get('currency', 'ron')
            
            if not cart_data:
                messages.error(request, 'Coșul este gol.')
                return redirect('marketplace:buy_credits')
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Calculate totals and prepare line items
            line_items = []
            total_credits = 0
            
            for item in cart_data:
                credits = item['credits']
                quantity = item['quantity']
                price = item['priceEur'] if currency == 'eur' else item['priceRon']
                
                total_credits += credits * quantity
                
                line_items.append({
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f'{credits} Credite Piata.ro',
                            'description': f'Pachet cu {credits} credite pentru promovarea anunțurilor',
                        },
                        'unit_amount': price * 100,  # Convert to cents
                    },
                    'quantity': quantity,
                })
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('marketplace:payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('marketplace:buy_credits')),
                metadata={
                    'user_id': request.user.id,
                    'total_credits': total_credits,
                    'cart_data': json.dumps(cart_data),
                    'currency': currency,
                }
            )
            
            # Create a Payment record before redirecting
            try:
                Payment.objects.create(
                    user=request.user,
                    payment_type='credits',
                    amount=Decimal(str(sum(item['price_data']['unit_amount'] * item['quantity'] for item in line_items) / 100)), # Calculate total amount from line items
                    currency=currency,
                    status='pending',
                    stripe_payment_intent_id=checkout_session.payment_intent, # Store the payment intent ID from the session
                    metadata={'checkout_session_id': checkout_session.id, 'cart_data': cart_data}
                )
            except Exception as payment_exc:
                # Log this error, but proceed with redirecting to Stripe for payment attempt
                # Consider how to handle if payment record creation fails critically
                print(f"Error creating Payment record: {payment_exc}")


            return redirect(checkout_session.url)
            
        except Exception as e:
            messages.error(request, f'Eroare la procesarea plății: {str(e)}')
            return redirect('marketplace:buy_credits')
    
    return redirect('marketplace:buy_credits')


@login_required
def promote_listing_view(request, listing_id):
    """Promote a listing to first page."""
    try:
        listing = Listing.objects.get(id=listing_id, user=request.user)
    except Listing.DoesNotExist:
        messages.error(request, 'Anunțul nu a fost găsit sau nu îți aparține.')
        return redirect('marketplace:profile')
    
    if request.method == 'POST':
        form = PromoteListingForm(request.POST)
        if form.is_valid():
            duration_days = int(form.cleaned_data['duration_days'])
            # Ensure credits_needed is a Decimal for precise calculations
            credits_needed = Decimal(str(duration_days * 0.5))
            
            user_profile = request.user.profile
            
            if user_profile.credits_balance >= credits_needed:
                if user_profile.deduct_credits(credits_needed): # Use the model's method
                    # Create ListingBoost record
                    # Assuming credits_cost (PositiveIntegerField) stores units of 0.5 credits.
                    # So, if credits_needed is 3.5, credits_cost_int will be 7.
                    credits_cost_int = int(credits_needed * 2)
                    ListingBoost.objects.create(
                        listing=listing,
                        boost_type='featured',
                        credits_cost=credits_cost_int, # Store as integer units of 0.5 credits
                        duration_days=duration_days
                    )

                    # Mark listing as featured
                    listing.is_featured = True
                    listing.save()

                    # Create CreditTransaction record
                    # Assuming amount (IntegerField) also stores units of 0.5 credits.
                    transaction_amount_int = int(credits_needed * 2)
                    CreditTransaction.objects.create(
                        user=request.user,
                        transaction_type='spent',
                        amount=-abs(transaction_amount_int), # Store as negative integer units of 0.5 credits
                        description=f"Promovare anunț: {listing.title} ({duration_days} zile, cost {credits_needed} credite)",
                        listing=listing
                    )

                    messages.success(request, f'Anunțul "{listing.title}" a fost promovat cu succes pentru {duration_days} zi(le)!')
                    return redirect('marketplace:listing_detail', listing_id=listing.id)
                else:
                    # This case should ideally not be reached if credits_balance check is correct
                    messages.error(request, 'A apărut o eroare la procesarea creditelor.')
            else:
                messages.error(request, 'Nu ai suficiente credite pentru această promovare.')
                return redirect('marketplace:buy_credits') # Redirect to buy credits page
    else:
        form = PromoteListingForm(initial={'listing_id': listing.id}) # Pass actual listing_id
    
    return render(request, 'marketplace/promote_listing.html', {
        'form': form,
        'listing': listing,
    })


# Legal Pages Views
def terms_of_service_view(request):
    """Terms of Service page."""
    return render(request, 'marketplace/legal/terms_of_service.html')


def privacy_policy_view(request):
    """Privacy Policy page."""
    return render(request, 'marketplace/legal/privacy_policy.html')


def contact_view(request):
    """Contact page with contact form."""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, just show a success message
        messages.success(request, 'Mesajul tău a fost trimis cu succes! Îți vom răspunde în cel mai scurt timp.')
        return redirect('marketplace:contact')
    
    return render(request, 'marketplace/legal/contact.html')


def about_view(request):
    """About Us page."""
    return render(request, 'marketplace/legal/about.html')


def help_view(request):
    """Help/FAQ page."""
    return render(request, 'marketplace/legal/help.html')


@login_required
def report_listing_view(request, listing_id):
    """Handle listing reports via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        listing = Listing.objects.get(id=listing_id)
    except Listing.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Anunțul nu a fost găsit'}, status=404)
    
    # Check if user already reported this listing
    if ListingReport.objects.filter(listing=listing, reporter=request.user).exists():
        return JsonResponse({'success': False, 'message': 'Ați raportat deja acest anunț'})
    
    # Users cannot report their own listings
    if listing.user == request.user:
        return JsonResponse({'success': False, 'message': 'Nu puteți raporta propriul anunț'})
    
    reason = request.POST.get('reason')
    comment = request.POST.get('comment', '')
    
    if not reason:
        return JsonResponse({'success': False, 'message': 'Vă rugăm să selectați un motiv'})
    
    # Create the report
    report = ListingReport.objects.create(
        listing=listing,
        reporter=request.user,
        reason=reason,
        comment=comment
    )
    
    return JsonResponse({
        'success': True, 
        'message': 'Raportul a fost trimis cu succes. Vă mulțumim pentru feedback!'
    })


def public_profile_view(request, username):
    """Public profile view for any user."""
    try:
        profile_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Utilizatorul nu a fost găsit.')
        return redirect('marketplace:home')
    
    # Get user's active listings
    user_listings = Listing.objects.filter(
        user=profile_user, 
        status='active'
    ).order_by('-created_at')
    
    # Get user profile
    try:
        user_profile = profile_user.profile
    except:
        # Create profile if it doesn't exist
        user_profile = UserProfile.objects.create(user=profile_user)
    
    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'user_listings': user_listings,
        'page_title': f'Profilul lui {profile_user.username}',
    }
    
    return render(request, 'marketplace/public_profile.html', context)


# Stripe Webhook Handler
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Generic webhook error', 'detail': str(e)}, status=500)

    # Handle the checkout.session.completed event
    if event.type == 'checkout.session.completed':
        session = event.data.object
        payment_intent_id = session.get('payment_intent')

        if not payment_intent_id:
            return JsonResponse({'error': 'Payment Intent ID missing in session.'}, status=400)

        try:
            # Retrieve the pending Payment record
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)

            if payment.status == 'succeeded':
                # Already processed by redirect or another webhook call
                return JsonResponse({'status': 'already processed'}, status=200)

            if payment.status == 'pending' and session.payment_status == 'paid':
                # Fulfill the purchase
                user = payment.user
                user_profile = user.profile

                metadata = session.get('metadata', {}) # Metadata from checkout session creation
                if not metadata: # Fallback to payment metadata if session metadata is empty
                    payment_metadata_db = payment.metadata
                    if isinstance(payment_metadata_db, str): # if metadata stored as JSON string
                        payment_metadata_db = json.loads(payment_metadata_db)
                    metadata = payment_metadata_db

                total_credits_str = metadata.get('total_credits', '0')
                cart_data_str = metadata.get('cart_data', '[]')

                try:
                    total_credits = int(total_credits_str)
                except ValueError:
                    total_credits = 0 # Or handle error appropriately

                try:
                    cart_data = json.loads(cart_data_str) if isinstance(cart_data_str, str) else cart_data_str
                    if not isinstance(cart_data, list): cart_data = []
                except json.JSONDecodeError:
                    cart_data = [] # Or handle error

                # Add credits to user profile
                user_profile.credits_balance += Decimal(str(total_credits))
                user_profile.save()

                # Create transaction records for each item in cart
                # This part requires cart_data from the payment's metadata
                for item in cart_data:
                    item_credits = item.get('credits', 0)
                    item_quantity = item.get('quantity', 0)
                    # Determine price based on currency stored with payment or session
                    item_price = item.get('priceEur') if payment.currency.upper() == 'EUR' else item.get('priceRon')

                    for _ in range(item_quantity):
                        CreditTransaction.objects.create(
                            user=user,
                            transaction_type='purchase',
                            amount=int(item_credits), # Assuming item_credits is whole number or needs scaling if fractional
                            description=f"Achiziție {item_credits} credite ({item_price} {payment.currency.upper()}) via webhook",
                            listing=None, # No specific listing for credit purchase
                            payment_intent_id=payment_intent_id
                        )

                # Update Payment status
                payment.status = 'succeeded'
                payment.save()

                # Optionally, send a confirmation email or notification here

                return JsonResponse({'status': 'success'}, status=200)
            else:
                # Payment not successful or status mismatch
                payment.status = 'failed' # Or map other Stripe statuses
                payment.save()
                return JsonResponse({'status': 'payment not successful or status mismatch'}, status=200) # Stripe expects 200 for acknowledged events

        except Payment.DoesNotExist:
            # This case should be rare if process_payment_view always creates a Payment record.
            # Could log this as an issue, or attempt to create the payment record here if enough info.
            print(f"Webhook received for payment_intent_id {payment_intent_id} but no Payment record found.")
            return JsonResponse({'error': 'Payment record not found for webhook.'}, status=404) # Or 200 if Stripe needs it
        except Exception as e:
            # Log the exception e
            print(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    # Handle other event types
    # elif event.type == 'payment_intent.succeeded':
    #     payment_intent = event.data.object
    # etc.

    return JsonResponse({'status': 'unhandled event type'}, status=200) # Acknowledge other events


def floating_chat_view(request):
    """Render the floating chat widget with API key."""
    from django.conf import settings
    import os
    print(f"Debug - DEEPSEEK_API_KEY in settings: {settings.DEEPSEEK_API_KEY}")  # Debug output
    print(f"Debug - DEEPSEEK_API_KEY in env: {os.getenv('DEEPSEEK_API_KEY')}")  # Additional debug
    context = {
        'deepseek_api_key': settings.DEEPSEEK_API_KEY.strip() if settings.DEEPSEEK_API_KEY else '',
    }
    response = render(request, 'floating_chat.html', context)
    print(f"Debug - Template context API key: {context['deepseek_api_key']}")  # Debug output
    return response
