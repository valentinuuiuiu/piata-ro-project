import os
import django
import numpy as np
import requests
from django.db import connection

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

# Import models
from marketplace.models_vector import ListingEmbedding
from marketplace.models import Listing
from django.conf import settings

def get_embedding_from_deepseek(text):
    """Get embedding from Deepseek API"""
    api_key = settings.DEEPSEEK_API_KEY
    if not api_key:
        print("❌ Deepseek API key not found in settings")
        return None
    
    url = "https://api.deepseek.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "deepseek-embed",
        "input": text,
        "encoding_format": "float"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]
    except Exception as e:
        print(f"❌ Error getting embedding from Deepseek API: {e}")
        return None

def generate_embeddings_for_listings():
    """Generate embeddings for all listings using Deepseek API"""
    print("Generating embeddings for listings...")
    
    # Get all listings without embeddings
    listings = Listing.objects.filter(embedding__isnull=True)
    print(f"Found {listings.count()} listings without embeddings")
    
    for listing in listings:
        print(f"Processing listing: {listing.title}")
        
        # Generate embeddings
        title_text = listing.title
        description_text = listing.description
        
        # Get embeddings from Deepseek API
        title_embedding = get_embedding_from_deepseek(title_text)
        if not title_embedding:
            print(f"❌ Failed to get title embedding for listing: {listing.title}")
            continue
        
        description_embedding = get_embedding_from_deepseek(description_text)
        if not description_embedding:
            print(f"❌ Failed to get description embedding for listing: {listing.title}")
            continue
        
        # Create combined embedding (average of title and description)
        combined_embedding = [(t + d) / 2 for t, d in zip(title_embedding, description_embedding)]
        
        # Create or update the embedding
        embedding, created = ListingEmbedding.objects.update_or_create(
            listing=listing,
            defaults={
                'title_embedding': title_embedding,
                'description_embedding': description_embedding,
                'combined_embedding': combined_embedding
            }
        )
        
        if created:
            print(f"✅ Created new embedding for listing: {listing.title}")
        else:
            print(f"✅ Updated embedding for listing: {listing.title}")

def search_similar_listings(query_text, limit=5):
    """Search for listings similar to the query text"""
    print(f"Searching for listings similar to: '{query_text}'")
    
    # Get embedding for query text
    query_embedding = get_embedding_from_deepseek(query_text)
    if not query_embedding:
        print("❌ Failed to get embedding for query text")
        return []
    
    # Search for similar listings
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT l.id, l.title, l.description, l.price, l.currency,
                   e.combined_embedding <-> CAST(%s AS vector) AS distance
            FROM marketplace_listing l
            JOIN marketplace_listingembedding e ON l.id = e.listing_id
            ORDER BY distance ASC
            LIMIT %s
            """,
            [query_embedding, limit]
        )
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return results

if __name__ == "__main__":
    # Check if Deepseek API key is available
    if not settings.DEEPSEEK_API_KEY:
        print("❌ Deepseek API key not found in settings. Please add it to .env file.")
        exit(1)
    
    # Generate embeddings for listings
    generate_embeddings_for_listings()
    
    # Search for similar listings
    query = "iPhone 13 Pro Max in perfect condition"
    similar_listings = search_similar_listings(query)
    
    print("\nSearch Results:")
    for i, listing in enumerate(similar_listings):
        print(f"{i+1}. {listing['title']} - {listing['price']} {listing['currency']}")
        print(f"   Distance: {listing['distance']:.4f}")
        print(f"   Description: {listing['description'][:100]}...")
        print()