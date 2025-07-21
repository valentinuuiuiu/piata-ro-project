from django.core.management.base import BaseCommand
from marketplace.models import Listing
from marketplace.models_vector import ListingEmbedding
from django.db import connection

class Command(BaseCommand):
    help = 'Create vector index for faster similarity searches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Drop existing index and recreate'
        )

    def handle(self, *args, **options):
        recreate = options['recreate']
        
        # Check if we have any embeddings
        if not ListingEmbedding.objects.exists():
            self.stdout.write(self.style.ERROR('No embeddings found. Run generate_embeddings command first.'))
            return
        
        with connection.cursor() as cursor:
            # Drop existing index if requested
            if recreate:
                self.stdout.write('Dropping existing index...')
                try:
                    cursor.execute('DROP INDEX IF EXISTS marketplace_listingembedding_combined_embedding_idx;')
                    self.stdout.write(self.style.SUCCESS('Existing index dropped'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error dropping index: {e}'))
            
            # Create index
            self.stdout.write('Creating vector index...')
            try:
                cursor.execute(
                    'CREATE INDEX IF NOT EXISTS marketplace_listingembedding_combined_embedding_idx ON marketplace_listingembedding USING ivfflat (combined_embedding vector_l2_ops) WITH (lists = 100);'
                )
                self.stdout.write(self.style.SUCCESS('Vector index created successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating index: {e}'))
                return
            
            # Analyze the table to update statistics
            self.stdout.write('Analyzing table...')
            try:
                cursor.execute('ANALYZE marketplace_listingembedding;')
                self.stdout.write(self.style.SUCCESS('Table analyzed successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error analyzing table: {e}'))
                return