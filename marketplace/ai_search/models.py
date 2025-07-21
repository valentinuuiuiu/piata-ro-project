"""
AI Search models - imports from main marketplace models
This file provides compatibility layer for AI search imports
"""

# Import from main marketplace models
from marketplace.models import Listing, Category
from marketplace.models_vector import ListingEmbedding

# Make these available for import within ai_search module
__all__ = ['Listing', 'Category', 'ListingEmbedding']
