from django.core.management.base import BaseCommand
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.db import connection
import numpy as np
import time

class Command(BaseCommand):
    help = 'Benchmark vector search performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queries',
            type=int,
            default=10,
            help='Number of random queries to run'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of results per query'
        )

    def handle(self, *args, **options):
        queries = options['queries']
        limit = options['limit']
        
        # Check if we have any embeddings
        if not ListingEmbedding.objects.exists():
            self.stdout.write(self.style.ERROR('No embeddings found. Run generate_embeddings command first.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Running {queries} random vector queries with limit {limit}'))
        
        # Run queries
        total_time = 0
        for i in range(queries):
            # Generate random query vector
            query_vector = np.random.rand(1536).astype(np.float32)
            
            # Run query with timing
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT l.id, l.title
                    FROM marketplace_listing l
                    JOIN marketplace_listingembedding e ON l.id = e.listing_id
                    ORDER BY e.combined_embedding <-> CAST(%s AS vector)
                    LIMIT %s
                    """,
                    [query_vector.tolist(), limit]
                )
                results = cursor.fetchall()
            end_time = time.time()
            
            query_time = end_time - start_time
            total_time += query_time
            
            self.stdout.write(f'Query {i+1}: {len(results)} results in {query_time:.4f} seconds')
        
        # Calculate average
        avg_time = total_time / queries
        self.stdout.write(self.style.SUCCESS(f'Average query time: {avg_time:.4f} seconds'))