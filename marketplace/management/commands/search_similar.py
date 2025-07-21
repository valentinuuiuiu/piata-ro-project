from django.core.management.base import BaseCommand
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.db import connection

class Command(BaseCommand):
    help = 'Search for similar listings using vector embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            'query',
            type=str,
            help='Query text to search for'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Limit the number of results'
        )

    def handle(self, *args, **options):
        query = options['query']
        limit = options['limit']
        
        # Check if we have any embeddings
        if not ListingEmbedding.objects.exists():
            self.stdout.write(self.style.ERROR('No embeddings found. Run generate_embeddings command first.'))
            return
        
        # Get embedding for query text
        from marketplace.management.commands.generate_embeddings import Command as EmbeddingCommand
        embedding_cmd = EmbeddingCommand()
        query_embedding = embedding_cmd.get_embedding_from_deepseek(query)
        
        if not query_embedding:
            self.stdout.write(self.style.ERROR('Failed to get embedding for query text'))
            return
        
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
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f'Search results for: "{query}"'))
        self.stdout.write('-' * 80)
        
        for i, listing in enumerate(results):
            self.stdout.write(f"{i+1}. {listing['title']} - {listing['price']} {listing['currency']}")
            self.stdout.write(f"   Distance: {listing['distance']:.4f}")
            self.stdout.write(f"   Description: {listing['description'][:100]}...")
            self.stdout.write('')