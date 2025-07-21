from django.core.management.base import BaseCommand
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.db import connection

class Command(BaseCommand):
    help = 'Show vector database statistics'

    def handle(self, *args, **options):
        # Check if we have any embeddings
        embedding_count = ListingEmbedding.objects.count()
        if embedding_count == 0:
            self.stdout.write(self.style.ERROR('No embeddings found. Run generate_embeddings command first.'))
            return
        
        # Get basic stats
        listing_count = Listing.objects.count()
        listings_with_embeddings = Listing.objects.filter(embedding__isnull=False).count()
        listings_without_embeddings = listing_count - listings_with_embeddings
        
        self.stdout.write(self.style.SUCCESS('Vector Database Statistics'))
        self.stdout.write('-' * 50)
        self.stdout.write(f'Total listings: {listing_count}')
        self.stdout.write(f'Listings with embeddings: {listings_with_embeddings} ({listings_with_embeddings/listing_count*100:.1f}%)')
        self.stdout.write(f'Listings without embeddings: {listings_without_embeddings} ({listings_without_embeddings/listing_count*100:.1f}%)')
        
        # Check for vector index
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'marketplace_listingembedding'
                AND indexdef LIKE '%vector%';
            """)
            indexes = cursor.fetchall()
        
        if indexes:
            self.stdout.write('\nVector Indexes:')
            for idx_name, idx_def in indexes:
                self.stdout.write(f'- {idx_name}')
                self.stdout.write(f'  {idx_def}')
        else:
            self.stdout.write(self.style.WARNING('\nNo vector indexes found. Run create_vector_index command to improve search performance.'))
        
        # Check pgvector extension
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            extension = cursor.fetchone()
        
        if extension:
            self.stdout.write(f'\npgvector extension: {extension[0]} version {extension[1]}')
        else:
            self.stdout.write(self.style.ERROR('\npgvector extension not installed!'))
        
        # Database size
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT pg_size_pretty(pg_total_relation_size('marketplace_listingembedding'));
            """)
            size = cursor.fetchone()[0]
        
        self.stdout.write(f'\nListingEmbedding table size: {size}')