from django.db import models
from pgvector.django import VectorField

# Embedding dimensions for sentence-transformers all-MiniLM-L6-v2 model
EMBEDDING_DIM = 384

class ListingEmbedding(models.Model):
    """Model to store vector embeddings for listings"""
    listing = models.OneToOneField('marketplace.Listing', on_delete=models.CASCADE, related_name='embedding')
    title_embedding = VectorField(dimensions=EMBEDDING_DIM)  # all-MiniLM-L6-v2 embeddings are 384 dimensions
    description_embedding = VectorField(dimensions=EMBEDDING_DIM)
    combined_embedding = VectorField(dimensions=EMBEDDING_DIM)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['listing']),
        ]
    
    def __str__(self):
        return f"Embedding for {self.listing.title}"