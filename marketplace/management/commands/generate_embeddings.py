from django.core.management.base import BaseCommand
import requests
import numpy as np
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate embeddings for listings using Deepseek API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of listings to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of embeddings for all listings'
        )

    def get_embedding_from_deepseek(self, text):
        """Get embedding from Deepseek API"""
        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR('Deepseek API key not found in settings'))
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
            self.stdout.write(self.style.ERROR(f'Error getting embedding from Deepseek API: {e}'))
            return None

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        
        # Check if Deepseek API key is available
        if not settings.DEEPSEEK_API_KEY:
            self.stdout.write(self.style.ERROR('Deepseek API key not found in settings. Please add it to .env file.'))
            return
        
        # Get listings to process
        if force:
            listings = Listing.objects.all()
        else:
            listings = Listing.objects.filter(embedding__isnull=True)
        
        if limit:
            listings = listings[:limit]
        
        self.stdout.write(self.style.SUCCESS(f'Found {listings.count()} listings to process'))
        
        # Process listings
        for i, listing in enumerate(listings):
            self.stdout.write(f'Processing listing {i+1}/{listings.count()}: {listing.title}')
            
            # Generate embeddings
            title_text = listing.title
            description_text = listing.description
            
            # Get embeddings from Deepseek API
            title_embedding = self.get_embedding_from_deepseek(title_text)
            if not title_embedding:
                self.stdout.write(self.style.ERROR(f'Failed to get title embedding for listing: {listing.title}'))
                continue
            
            description_embedding = self.get_embedding_from_deepseek(description_text)
            if not description_embedding:
                self.stdout.write(self.style.ERROR(f'Failed to get description embedding for listing: {listing.title}'))
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
                self.stdout.write(self.style.SUCCESS(f'Created new embedding for listing: {listing.title}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated embedding for listing: {listing.title}'))
        
        self.stdout.write(self.style.SUCCESS('Done generating embeddings'))