from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.cache import cache_page
from .utils.cache_utils import ListingCache, SearchCache
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
import logging
from .views.messaging import floating_chat_view, messages_view, conversation_view, send_message_view
# Note: stripe will be installed separately
try:
    import stripe
    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None

from .models import Category, Favorite, Listing, Message, UserProfile, ListingImage, CreditPackage, Payment, CreditTransaction, ListingBoost, ListingReport
from .serializers import (
    CategorySerializer,
    ListingSerializer,
    FavoriteCreateSerializer,
    FavoriteSerializer,
    ListingCreateSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from .forms import ListingForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm, PromoteListingForm

# Configure logger
logger = logging.getLogger(__name__)

# Configure Stripe
if stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):  # type: ignore[override]
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
        serializer = CategorySerializer(subcategories, many=True)
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

    def get_queryset(self):  # type: ignore[override]
        queryset = Listing.objects.all()

        params = getattr(self.request, 'query_params', self.request.GET)

        # Filter by status (default to active)
        status_val = params.get("status", "active")
        if status_val and status_val != "all":
            queryset = queryset.filter(status=status_val)

        # Filter by category (accept category id)
        category_id = params.get("category")
        if category_id:
            queryset = queryset.filter(Q(category_id=category_id) | Q(subcategory_id=category_id))

        # Filter by price range
        min_price = params.get("min_price")
        max_price = params.get("max_price")
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass

        # Filter by location
        location = params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Try to use cached search results if available
        try:
            cache_filters = {
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price,
                "location": location,
            }
            cached_results = SearchCache.get_search_results(status_val, cache_filters)
            if cached_results:
                return Listing.objects.filter(id__in=[l.id for l in cached_results])
        except Exception:
            # Non-fatal: ignore cache errors
            pass

        return queryset

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

    def get_queryset(self):  # type: ignore[override]
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in ["create", "update", "partial_update"]:
            return MessageCreateSerializer
        return MessageSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):  # type: ignore[override]
        return Favorite.objects.filter(user=self.request.user)

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in ["create", "update", "partial_update"]:
            return FavoriteCreateSerializer
        return FavoriteSerializer


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=True, methods=["get"])
    def listings(self, request, pk=None):
        user = self.get_object()
        listings = Listing.objects.filter(user=user)
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = UserProfileSerializer(user.userprofile)
        return Response(serializer.data)





# Frontend Views for the Comprehensive Marketplace

def home_view(request):
    """Homepage view with enhanced functionality."""
    # Get all categories for the dropdown (only parent categories)
    categories = Category.objects.filter(parent__isnull=True).order_by('name')

    # Get featured/promoted listings
    featured_listings = Listing.objects.filter(
        status="active", is_featured=True
    ).order_by("-created_at")[:8]

    # Get recent listings (by date only)
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
        "user": request.user,
    }

    return render(request, "marketplace/index.html", context)


def categories_view(request):
    """Categories listing page."""
    from django.db.models import Count, Q

    # Annotate categories with active listing counts
    categories = Category.objects.filter(parent__isnull=True).prefetch_related(
        'subcategories'
    ).annotate(
        listings_count=Count('listings', filter=Q(listings__status='active'))
    )

    # Annotate subcategories with active listing counts
    for category in categories:
        subcategories = list(category.subcategories.all())
        for subcategory in subcategories:
            subcategory.listings_count = Listing.objects.filter(category=subcategory, status='active').count()
        category.subcategories_list = subcategories

    context = {
        "categories": categories,
        "page_title": "Toate categoriile",
    }
    
    return render(request, "marketplace/categories.html", context)


@cache_page(60 * 15)  # Cache for 15 minutes
def category_detail_view(request, category_slug):
    """Optimized category detail page with listings."""
    from django.shortcuts import get_object_or_404
    from django.core.paginator import Paginator
    
    category = get_object_or_404(
        Category.objects.select_related('parent'),
        slug=category_slug
    )
    
    # Get cached subcategories
    subcategories = Category.objects.filter(parent=category).only('id', 'name', 'slug')
    
    # Get optimized listings
    listings = Listing.objects.filter(
        category_id__in=[category.id] + list(subcategories.values_list('id', flat=True)),
        status="active"
    ).select_related('category', 'user').order_by(
        "category_id" if subcategories.exists() else "",
        "-is_featured", 
        "-created_at"
    )
    
    # Paginate with optimized query
    paginator = Paginator(listings, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
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
    subcategory_id = request.GET.get('subcategory', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')

    if search_query:
        listings = listings.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_id:
        category = Category.objects.get(id=category_id)
        cat_ids = [category.id]
        subcats = Category.objects.filter(parent=category)
        cat_ids.extend(subcats.values_list('id', flat=True))
        listings = listings.filter(Q(category_id__in=cat_ids) | Q(subcategory_id__in=cat_ids))

    if subcategory_id:
        listings = listings.filter(subcategory_id=subcategory_id)

    if min_price:
        try:
            listings = listings.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            listings = listings.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
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
        "selected_subcategory": subcategory_id,
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
    
    # Get all images for this listing
    listing_images = ListingImage.objects.filter(listing=listing).order_by('order', 'id')
    
    # Get related listings
    related_listings = Listing.objects.filter(
        category=listing.category,
        status="active"
    ).exclude(id=listing.id)[:6]
    
    context = {
        "listing": listing,
        "listing_images": listing_images,
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
            # Ensure listing id is serializable
            return redirect('marketplace:listing_detail', listing_id=str(getattr(listing, 'id', '')))
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
    profile_form = UserProfileForm(instance=getattr(request.user, 'profile', None))
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=getattr(request.user, 'profile', None))

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


# Moved to messaging.py


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
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    location = request.GET.get('location', '')
    sort_by = request.GET.get('sort', '-featured')
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
            user_latitude = float(user_lat)
            user_longitude = float(user_lng)
            distance_km = float(distance)
            user_location = Point(user_longitude, user_latitude, srid=4326)

            listings = listings.filter(
                location_point__dwithin=(user_location, distance_km * 1000)
            ).annotate(
                distance=Distance('location_point', user_location)
            ).order_by('distance')

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
        # Sorting by distance is already handled by the annotation and order_by above
        pass
    else:  # -created_at (default)
        listings = listings.order_by('-created_at')
    
    # Handle pagination
    from django.core.paginator import Paginator
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Compute total results for pagination summary
    try:
        total_results = page_obj.paginator.count
    except Exception:
        total_results = len(list(page_obj))

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
    "total_results": total_results,
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
    user_profile = getattr(request.user, 'profile', None)
    credit_packages = CreditPackage.objects.filter(is_active=True).order_by('credits')
    recent_transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'user_profile': user_profile,
        'credit_packages': credit_packages,
        'recent_transactions': recent_transactions,
        'promotion_cost': Decimal('0.50'),  # Cost to promote a listing
    }
    return render(request, 'marketplace/credits_cart.html', context)

# Functions moved to payments.py

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
                # Get metadata from session (session.metadata may be None or a dict-like object)
                session_metadata = {}
                if hasattr(session, 'metadata') and session.metadata:
                    try:
                        session_metadata = session.metadata
                    except Exception:
                        session_metadata = {}

                user_id = session_metadata.get('user_id') if isinstance(session_metadata, dict) else None
                try:
                    total_credits = int(session_metadata.get('total_credits', 0)) if isinstance(session_metadata, dict) else 0
                except (ValueError, TypeError):
                    total_credits = 0

                try:
                    cart_data = json.loads(session_metadata.get('cart_data', '[]')) if isinstance(session_metadata, dict) else []
                except (TypeError, json.JSONDecodeError):
                    cart_data = []

                currency = session_metadata.get('currency', 'ron') if isinstance(session_metadata, dict) else 'ron'
                
                # Verify user
                if str(request.user.id) != user_id:
                    messages.error(request, "Sesiunea de plată nu corespunde cu utilizatorul curent.")
                    return redirect('marketplace:buy_credits')
                
                # Add credits to user profile
                user_profile = getattr(request.user, 'profile', None)
                if user_profile is not None:
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



@login_required
def credits_history(request):
    """View credit transaction history"""
    transactions = CreditTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'transactions': transactions,
    'user_profile': getattr(request.user, 'profile', None)
    }
    return render(request, 'marketplace/credits_history.html', context)


@login_required
def process_payment_view(request):
    """Process Stripe payment for credits from shopping cart."""
    if request.method == 'POST':
        import json
        
        try:
            # Get cart data from the form
            cart_data = json.loads(request.POST.get('cart_data', '[]'))
            currency = request.POST.get('currency', 'ron')
            
            if not cart_data:
                messages.error(request, 'Coșul este gol.')
                return redirect('marketplace:buy_credits')
            
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
                        'unit_amount': int(price * 100),  # Convert to cents
                    },
                    'quantity': quantity,
                })
            
            # Create Stripe checkout session
            if stripe is None:
                messages.error(request, 'Stripe is not configured on the server.')
                return redirect('marketplace:home')

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('marketplace:payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('marketplace:home')),
                metadata={
                    'user_id': str(request.user.id),
                    'total_credits': str(total_credits),
                    'cart_data': json.dumps(cart_data),
                    'currency': currency,
                }
            )
            
            # Some stripe versions return url directly, others require .url attribute
            redirect_url = getattr(checkout_session, 'url', None) or checkout_session.get('url') if isinstance(checkout_session, dict) else None
            if not redirect_url:
                # Fallback to hosted_session_url or object URL
                redirect_url = getattr(checkout_session, 'url', None) or getattr(checkout_session, 'hosted_url', None)
            return redirect(redirect_url or 'marketplace:home')
            
        except Exception as e:
            messages.error(request, f'Eroare la procesarea plății: {str(e)}')
            print(f"Stripe error: {str(e)}")  # Debug
            return redirect('marketplace:home')
    
    return redirect('marketplace:home')


@login_required
def promote_listing_view(request, listing_id):
    """Promote a listing to first page with atomic transaction handling."""
    try:
        listing = Listing.objects.get(id=listing_id, user=request.user)
    except Listing.DoesNotExist:
        messages.error(request, 'Anunțul nu a fost găsit sau nu îți aparține.')
        return redirect('marketplace:profile')
    
    # Check if listing is already featured
    if listing.is_featured:
        messages.info(request, 'Acest anunț este deja promovat.')
        return redirect('marketplace:listing_detail', listing_id=str(listing.id))
    
    # Determine the target category
    target_category = listing.category
    category_name = target_category.name
    
    if request.method == 'POST':
        form = PromoteListingForm(request.POST)
        
        if form.is_valid():
            duration_days = int(form.cleaned_data['duration_days'])
            credits_needed = Decimal(str(duration_days * 0.5))
            auto_repost_interval = request.POST.get('auto_repost_interval', 'none')
            
            user_profile = getattr(request.user, 'profile', None)

            # Check if user_profile exists and has enough credits
            if user_profile is None or user_profile.credits_balance < credits_needed:
                messages.error(request, f'Nu ai suficiente credite. Ai nevoie de {credits_needed} credite pentru promovare.')
                return redirect('marketplace:credits_dashboard')
            
            # Use atomic transaction to ensure data consistency
            try:
                with transaction.atomic():
                    # Lock user profile to prevent race conditions
                    user_profile = UserProfile.objects.select_for_update().get(user=request.user)
                    
                    # Double-check credits after locking
                    if user_profile.credits_balance < credits_needed:
                        messages.error(request, 'Nu ai suficiente credite. Încearcă din nou.')
                        return redirect('marketplace:credits_dashboard')
                    
                    # Deduct credits safely
                    user_profile.deduct_credits(credits_needed)
                    
                    # Calculate expiration time
                    expires_at = timezone.now() + timedelta(days=duration_days)
                    
                    # Create ListingBoost record
                    boost = ListingBoost.objects.create(
                        listing=listing,
                        boost_type='featured',
                        credits_cost=int(credits_needed * 2),  # Store as integer (0.5 credits = 1)
                        duration_days=duration_days,
                        starts_at=timezone.now(),
                        expires_at=expires_at,
                        is_active=True
                    )
                    
                    # Mark listing as featured
                    listing.is_featured = True
                    listing.save()
                    
                    # Create transaction record
                    CreditTransaction.objects.create(
                        user=request.user,
                        transaction_type='spent',
                        amount=credits_needed,
                        description=f"Promovare {duration_days} zile în categoria '{category_name}': {listing.title}",
                        listing=listing
                    )
                    
                    # Handle auto-repost if selected
                    if auto_repost_interval != 'none':
                        from .tasks import auto_repost_listing
                        # Ensure the task supports delay and listing id is string
                        try:
                            listing_id_str = str(getattr(listing, 'id', ''))
                            if hasattr(auto_repost_listing, 'delay'):
                                auto_repost_listing.delay(listing_id_str, auto_repost_interval)
                        except Exception:
                            logger.exception('Failed to schedule auto repost')
                        boost.auto_repost = True
                        boost.save(update_fields=['auto_repost'])
                        messages.success(request, f'Repromovarea automată a fost activată - anunțul va fi repostat la fiecare {auto_repost_interval} minute.')
                    
                    messages.success(
                        request, 
                        f'Anunțul "{listing.title}" a fost promovat pentru {duration_days} zile! '
                        f'Acum apare primul în categoria "{category_name}" până pe {expires_at.strftime("%d.%m.%Y")}.'
                    )
                    
                    return redirect('marketplace:listing_detail', listing_id=str(getattr(listing, 'id', '')))
                    
            except Exception as e:
                messages.error(request, 'A apărut o eroare la procesarea promovării. Te rugăm să încerci din nou.')
                logger.error(f"Promote listing error for user {request.user.id}, listing {listing_id}: {str(e)}")
                return redirect('marketplace:promote_listing', listing_id=listing_id)
        else:
            messages.error(request, 'Formularul conține erori. Te rugăm să verifici datele introduse.')
    else:
        # GET request - show form
        form = PromoteListingForm(initial={'listing_id': listing_id})
    
    context = {
        'form': form,
        'listing': listing,
        'target_category': category_name,
        'promotion_cost': Decimal('0.5'),
    'user_credits': getattr(getattr(request.user, 'profile', None), 'credits_balance', 0),
        'existing_boosts': listing.boosts.filter(is_active=True)
    }
    
    return render(request, 'marketplace/promote_listing.html', context)


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
    user_profile = getattr(profile_user, 'profile', None)
    if user_profile is None:
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
        if stripe is None:
            raise RuntimeError("Stripe library is not available")
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        # If stripe is available, check for signature verification
        if stripe is not None and hasattr(stripe, 'error') and hasattr(stripe.error, 'SignatureVerificationError') and isinstance(e, stripe.error.SignatureVerificationError):
            return JsonResponse({'error': str(e)}, status=400)
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

            # Determine payment_status in a defensive way (session may be stripe object or dict)
            payment_status = getattr(session, 'payment_status', None) if not isinstance(session, dict) else session.get('payment_status')
            if payment.status == 'pending' and payment_status == 'paid':
                # Fulfill the purchase
                user = payment.user
                user_profile = getattr(user, 'profile', None)

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

                # Add credits to user profile (guarded)
                if user_profile is not None:
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
