from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Listing, Category, ListingImage, UserProfile


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ListingForm(forms.ModelForm):
    """Form for creating and editing listings."""
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'hidden',
            'id': 'id_images',
            'accept': 'image/*'
        }),
        label='Imagini',
        help_text='Poți selecta mai multe imagini. Prima imagine va fi imaginea principală.',
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
            'id': 'id_category'
        }),
        label='Categoria *'
    )
    subcategory = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
            'id': 'id_subcategory'
        }),
        label='Subcategoria'
    )
    
    # Location fields with enhanced functionality
    use_current_location = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-primary shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50',
            'id': 'id_use_current_location'
        }),
        label='Folosește locația mea actuală'
    )
    
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'currency', 'location', 'address', 
            'city', 'county', 'postal_code', 'latitude', 'longitude',
            'category', 'subcategory'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Titlul anunțului'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'rows': 6,
                'placeholder': 'Descrie produsul sau serviciul...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'currency': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Localitatea (va fi completată automat)',
                'readonly': True
            }),
            'address': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Strada, numărul (opțional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Orașul',
                'id': 'id_city',
                'list': 'city-datalist'
            }),
            'county': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Județul',
                'id': 'id_county'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Codul poștal (opțional)'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
        labels = {
            'title': 'Titlu *',
            'description': 'Descriere *',
            'price': 'Preț',
            'currency': 'Monedă',
            'location': 'Locația',
            'address': 'Adresa',
            'city': 'Orașul *',
            'county': 'Județul',
            'postal_code': 'Cod poștal',
            'category': 'Categoria *',
            'subcategory': 'Subcategoria',
        }
        help_texts = {
            'location': 'Se va completa automat pe baza orașului selectat',
            'city': 'Selectează orașul unde se află produsul',
            'address': 'Adresa exactă (opțional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Currency choices
        self.fields['currency'].choices = [
            ('RON', 'Lei (RON)'),
            ('EUR', 'Euro (EUR)'),
            ('USD', 'Dolari (USD)'),
        ]

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        if subcategory and category and subcategory.parent != category:
            raise forms.ValidationError({
                'subcategory': "Subcategoria selectată nu aparține categoriei alese. Vă rugăm să selectați o subcategorie validă."
            })
        return cleaned_data

    def save(self, commit=True):
        from marketplace.location_services import LocationService
        
        listing = super().save(commit=False)
        
        # Auto-populate location field based on city and county
        if listing.city:
            location_parts = [listing.city]
            if listing.county:
                location_parts.append(listing.county)
            listing.location = ', '.join(location_parts)
        
        # Try to geocode if coordinates aren't provided
        if not listing.latitude or not listing.longitude:
            if listing.city or listing.address:
                geocoded = LocationService.geocode_address(
                    listing.address or '', 
                    listing.city or ''
                )
                if geocoded:
                    listing.latitude = geocoded['latitude']
                    listing.longitude = geocoded['longitude']
                    listing.location_verified = True
                    
                    # Fill in missing location data
                    if not listing.city and geocoded.get('city'):
                        listing.city = geocoded['city']
                    if not listing.county and geocoded.get('county'):
                        listing.county = geocoded['county']
        
        if commit:
            listing.save()
            
            # Handle image uploads
            images = self.files.getlist('images')
            for idx, image in enumerate(images):
                ListingImage.objects.create(
                    listing=listing,
                    image=image,
                    is_main=(idx == 0),
                    order=idx
                )
        
        return listing


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
            'placeholder': 'email@exemplu.com'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Alege un nume de utilizator'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
            'placeholder': 'Parola ta'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
            'placeholder': 'Confirmă parola'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information."""
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'rows': 4,
                'placeholder': 'Spune-ne ceva despre tine...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': '+40 xxx xxx xxx'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Orașul tău'
            }),
        }
        labels = {
            'bio': 'Descriere',
            'phone': 'Numărul de telefon',
            'location': 'Localitatea',
        }
        help_texts = {
            'phone': 'Numărul tău de telefon va fi afișat în anunțurile tale',
            'bio': 'Poți scrie o scurtă descriere despre tine',
            'location': 'Localitatea în care te afli'
        }

# Alias for backward compatibility
ProfileForm = UserProfileForm


class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Prenumele'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'Numele de familie'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'placeholder': 'email@exemplu.com'
            }),
        }
        labels = {
            'first_name': 'Prenume',
            'last_name': 'Nume',
            'email': 'Email',
        }


class CreditPurchaseForm(forms.Form):
    """Form for purchasing credits - 1 Credit = 1€ = 5 RON."""
    CREDIT_PACKAGES = [
        (1, '1 Credit - 1€ / 5 RON'),
        (5, '5 Credite - 5€ / 25 RON'),
        (10, '10 Credite - 10€ / 50 RON'),
        (20, '20 Credite - 20€ / 100 RON'),
        (50, '50 Credite - 50€ / 250 RON'),
    ]
    
    credits = forms.ChoiceField(
        choices=CREDIT_PACKAGES,
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300'
        }),
        label='Selectează numărul de credite'
    )
    
    currency = forms.ChoiceField(
        choices=[
            ('eur', 'EUR - Euro'),
            ('ron', 'RON - Lei')
        ],
        initial='ron',
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300'
        }),
        label='Moneda de plată'
    )


class PromoteListingForm(forms.Form):
    """Form for promoting listings to first page - 0.5 credits."""
    listing_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    duration_days = forms.ChoiceField(
        choices=[
            (1, '1 zi - 0.5 credite'),
            (3, '3 zile - 1.5 credite'),
            (7, '7 zile - 3.5 credite'),
            (14, '14 zile - 7 credite'),
            (30, '30 zile - 15 credite'),
        ],
        initial=1,
        widget=forms.RadioSelect(attrs={
            'class': 'h-4 w-4 text-primary focus:ring-primary border-gray-300'
        }),
        label='Durata promovării pe prima pagină'
    )
    
    def get_credit_cost(self):
        """Calculate credits needed based on duration."""
        duration = int(self.cleaned_data.get('duration_days', 1))
        return duration * 0.5




class ReportForm(forms.ModelForm):
    """Form for reporting inappropriate listings"""
    class Meta:
        from marketplace.models import Report
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm',
                'rows': 4,
                'placeholder': 'Descrieți problema întâlnită...'
            })
        }
        labels = {
            'reason': 'Motivul raportului',
            'description': 'Descriere detaliată'
        }

class StripePaymentForm(forms.Form):

    """Form to handle Stripe payment for credits."""
    credits_to_buy = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    currency = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    total_amount = forms.DecimalField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def get_amount_in_cents(self):
        """Convert amount to cents for Stripe."""
        return int(self.cleaned_data['total_amount'] * 100)
