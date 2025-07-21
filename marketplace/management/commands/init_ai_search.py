"""
Management command to initialize AI search system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from marketplace.models import Listing, ListingImage
from marketplace.ai_search.enhanced_search import search_engine
from marketplace.ai_search.image_recognition import image_recognition
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize AI search system - generate embeddings and process images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of listings to process in each batch'
        )
        parser.add_argument(
            '--force-rebuild',
            action='store_true',
            help='Force rebuild all embeddings even if they exist'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Skip image processing'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Process only listings from specific category'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force_rebuild = options['force_rebuild']
        skip_images = options['skip_images']
        category = options['category']

        self.stdout.write(self.style.SUCCESS('Starting AI search initialization...'))

        # Get listings to process
        listings = Listing.objects.filter(is_active=True)
        if category:
            listings = listings.filter(category__name__icontains=category)
        
        total_listings = listings.count()
        self.stdout.write(f'Processing {total_listings} listings...')

        processed = 0
        failed = 0

        for i in range(0, total_listings, batch_size):
            batch = listings[i:i+batch_size]
            
            for listing in batch:
                try:
                    with transaction.atomic():
                        # Generate embeddings
                        if force_rebuild or not hasattr(listing, 'embedding'):
                            # Create embedding for the listing
                            text = f"{listing.title} {listing.description}"
                            embedding = search_engine.encode_text(text)
                            
                            from marketplace.models_vector import ListingEmbedding
                            ListingEmbedding.objects.update_or_create(
                                listing=listing,
                                defaults={
                                    'combined_embedding': embedding,
                                    'title_embedding': search_engine.encode_text(listing.title),
                                    'description_embedding': search_engine.encode_text(listing.description)
                                }
                            )
                        
                        # Process images
                        if not skip_images and ListingImage.objects.filter(listing=listing).exists():
                            image_recognition.auto_tag_listing(listing)
                        
                        processed += 1
                        
                        if processed % 10 == 0:
                            self.stdout.write(
                                f'Processed {processed}/{total_listings} listings...'
                            )
                            
                except Exception as e:
                    logger.error(f"Error processing listing {listing.id}: {e}")
                    failed += 1
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f'AI search initialization complete! '
                f'Processed: {processed}, Failed: {failed}'
            )
        )
