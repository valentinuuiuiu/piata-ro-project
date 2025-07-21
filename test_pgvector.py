import os
import django
import numpy as np
from django.db import connection

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

# Monkey patch the Category.save method to avoid using cache
from marketplace.models import Category
original_save = Category.save

def save_without_cache(self, *args, **kwargs):
    # Skip the cache invalidation
    super(Category, self).save(*args, **kwargs)

Category.save = save_without_cache

# Import models
from marketplace.models_vector import ListingEmbedding
from marketplace.models import Listing

def test_pgvector():
    """Test pgvector functionality"""
    print("Testing pgvector functionality...")
    
    # Check if the vector extension is installed
    with connection.cursor() as cursor:
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("✅ pgvector extension is installed")
        else:
            print("❌ pgvector extension is NOT installed")
    
    # Get a listing or create one if none exists
    listing = Listing.objects.first()
    if not listing:
        print("Creating a test listing...")
        from django.contrib.auth.models import User
        
        # Create a user if none exists
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username="testuser",
                email="test@example.com",
                password="password123"
            )
        
        # Create a category if none exists
        category = Category.objects.first()
        if not category:
            category = Category.objects.create(
                name="Test Category",
                slug="test-category"
            )
        
        # Create a listing
        listing = Listing.objects.create(
            title="Test Listing",
            description="This is a test listing for pgvector",
            price=100.00,
            currency="RON",
            location="Test Location",
            user=user,
            category=category
        )
        print(f"Created listing: {listing.title}")
    
    # Create random embeddings
    title_embedding = np.random.rand(1536).astype(np.float32)
    description_embedding = np.random.rand(1536).astype(np.float32)
    combined_embedding = (title_embedding + description_embedding) / 2
    
    # Create or update the embedding
    embedding, created = ListingEmbedding.objects.update_or_create(
        listing=listing,
        defaults={
            'title_embedding': title_embedding.tolist(),
            'description_embedding': description_embedding.tolist(),
            'combined_embedding': combined_embedding.tolist()
        }
    )
    
    if created:
        print(f"✅ Created new embedding for listing: {listing.title}")
    else:
        print(f"✅ Updated embedding for listing: {listing.title}")
    
    # Test vector search
    print("\nTesting vector search...")
    query_vector = np.random.rand(1536).astype(np.float32)
    
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM marketplace_listingembedding ORDER BY combined_embedding <-> CAST(%s AS vector) LIMIT 5",
            [query_vector.tolist()]
        )
        results = cursor.fetchall()
        print(f"Found {len(results)} similar listings")
        
    print("\npgvector test completed successfully!")

if __name__ == "__main__":
    test_pgvector()
    
    # Restore original save method
    Category.save = original_save