from django.core.management.base import BaseCommand
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.db import connection
import numpy as np

class Command(BaseCommand):
    help = 'Generate random embeddings for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of random embeddings to generate'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get listings without embeddings
        listings = Listing.objects.filter(embedding__isnull=True)[:count]
        
        if not listings:
            self.stdout.write(self.style.ERROR('No listings found without embeddings'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Generating random embeddings for {len(listings)} listings'))
        
        for listing in listings:
            # Generate random embeddings
            title_embedding = np.random.rand(1536).astype(np.float32)
            description_embedding = np.random.rand(1536).astype(np.float32)
            combined_embedding = (title_embedding + description_embedding) / 2
            
            # Create embedding
            embedding = ListingEmbedding.objects.create(
                listing=listing,
                title_embedding=title_embedding.tolist(),
                description_embedding=description_embedding.tolist(),
                combined_embedding=combined_embedding.tolist()
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created random embedding for listing: {listing.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'Generated {len(listings)} random embeddings'))