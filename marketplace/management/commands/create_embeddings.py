from django.core.management.base import BaseCommand
from django.db import transaction
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from marketplace.ai_search.enhanced_search import search_engine
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create vector embeddings for all listings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of listings to process in each batch'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate embeddings even if they already exist'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force = options['force']
        
        self.stdout.write("🔮 Creating vector embeddings for listings...")
        
        # Get listings that need embeddings
        if force:
            listings = Listing.objects.filter(status='active')
            # Delete existing embeddings if force is True
            ListingEmbedding.objects.all().delete()
        else:
            # Only process listings without embeddings
            listings = Listing.objects.filter(
                status='active',
                embedding__isnull=True
            )
        
        total_listings = listings.count()
        self.stdout.write(f"📊 Found {total_listings} listings to process")
        
        if total_listings == 0:
            self.stdout.write("✅ All listings already have embeddings!")
            return
        
        processed = 0
        errors = 0
        
        # Process in batches
        for i in range(0, total_listings, batch_size):
            batch = listings[i:i + batch_size]
            
            with transaction.atomic():
                for listing in batch:
                    try:
                        # Create combined text for embedding
                        text = f"{listing.title} {listing.description}"
                        if listing.category:
                            text += f" {listing.category.name}"
                        if listing.location:
                            text += f" {listing.location}"
                        
                        # Generate embeddings
                        title_vector = search_engine.encode_text(listing.title)
                        description_vector = search_engine.encode_text(listing.description)
                        combined_vector = search_engine.encode_text(text)
                        
                        # Create or update embedding
                        embedding, created = ListingEmbedding.objects.get_or_create(
                            listing=listing,
                            defaults={
                                'title_embedding': title_vector,
                                'description_embedding': description_vector,
                                'combined_embedding': combined_vector,
                            }
                        )
                        
                        if not created and force:
                            embedding.title_embedding = title_vector
                            embedding.description_embedding = description_vector
                            embedding.combined_embedding = combined_vector
                            embedding.save()
                        
                        processed += 1
                        
                        if processed % 10 == 0:
                            self.stdout.write(f"📈 Processed {processed}/{total_listings} listings")
                            
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error creating embedding for listing {listing.id}: {e}")
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Error processing listing {listing.id}: {e}")
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Completed! Processed {processed} listings with {errors} errors"
            )
        )
        
        if errors > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"💡 Tip: Run again with --force to retry failed embeddings"
                )
            )
