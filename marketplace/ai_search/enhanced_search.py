"""
Enhanced Semantic Search for Piata.ro Marketplace
Combines vector search with traditional keyword search for superior results
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, F
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from pgvector.django import CosineDistance
import logging
from sentence_transformers import SentenceTransformer

from marketplace.models import Listing, Category
from marketplace.models_vector import ListingEmbedding

logger = logging.getLogger(__name__)

class EnhancedSemanticSearch:
    """
    Advanced search combining:
    - Vector similarity search
    - Full-text search
    - Geospatial search
    - Category filtering
    - Price range filtering
    """
    
    def __init__(self):
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            self.model_available = True
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer model: {e}")
            self.model = None
            self.model_available = False
        
    def encode_text(self, text: str) -> np.ndarray:
        """Convert text to vector embedding"""
        if not self.model_available or self.model is None:
            # Return dummy vector if model not available
            return np.zeros(384, dtype=np.float32)
        
        try:
            return np.array(self.model.encode(text, normalize_embeddings=True), dtype=np.float32)
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return np.zeros(384, dtype=np.float32)
    
    def hybrid_search(
        self,
        query: str,
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining multiple search strategies
        """
        try:
            # Step 1: Vector similarity search (fallback to empty if unavailable)
            vector_results = []
            if self.model_available:
                vector_results = self._vector_search(query, limit * 3)
            
            # Step 2: Full-text search (always available)
            text_results = self._full_text_search(query, limit * 3)
            
            # Step 3: Combine and rank results
            combined_results = self._combine_results(vector_results, text_results)
            
            # Step 4: Apply filters
            filtered_results = self._apply_filters(
                combined_results,
                category=category,
                location=location,
                min_price=min_price,
                max_price=max_price,
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km
            )
            
            # Step 5: Final ranking and pagination
            final_results = filtered_results[offset:offset + limit]
            
            return {
                'results': final_results,
                'total_count': len(filtered_results),
                'has_more': len(filtered_results) > offset + limit,
                'search_metadata': {
                    'query': query,
                    'vector_matches': len(vector_results),
                    'text_matches': len(text_results),
                    'final_matches': len(final_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return {'results': [], 'total_count': 0, 'error': str(e)}
    
    def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            query_vector = self.encode_text(query)
            
            # Find similar listings using cosine similarity
            similar_listings = ListingEmbedding.objects.annotate(
                similarity=1 - CosineDistance('combined_embedding', query_vector)
            ).filter(
                similarity__gt=0.3  # Minimum similarity threshold
            ).order_by('-similarity')[:limit]
            
            results = []
            for embedding in similar_listings:
                similarity = getattr(embedding, 'similarity', 0.0)
                results.append({
                    'listing': embedding.listing,
                    'score': float(similarity),
                    'type': 'vector'
                })
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def _full_text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Perform full-text search using PostgreSQL"""
        try:
            search_vector = SearchVector('title', weight='A') + \
                          SearchVector('description', weight='B')
            search_query = SearchQuery(query)
            
            results = Listing.objects.annotate(
                rank=SearchRank(search_vector, search_query)
            ).filter(
                rank__gt=0.1,
                status='active'
            ).order_by('-rank')[:limit]
            
            search_results = []
            for listing in results:
                rank = getattr(listing, 'rank', 0.0)
                search_results.append({
                    'listing': listing,
                    'score': float(rank),
                    'type': 'text'
                })
            return search_results
            
        except Exception as e:
            logger.error(f"Full-text search error: {e}")
            return []
    
    def _combine_results(
        self, 
        vector_results: List[Dict], 
        text_results: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate results from different search methods"""
        combined = {}
        
        # Add vector results
        for result in vector_results:
            listing_id = result['listing'].id
            if listing_id not in combined:
                combined[listing_id] = {
                    'listing': result['listing'],
                    'vector_score': result['score'],
                    'text_score': 0,
                    'final_score': result['score']
                }
            else:
                combined[listing_id]['vector_score'] = result['score']
        
        # Add text results
        for result in text_results:
            listing_id = result['listing'].id
            if listing_id not in combined:
                combined[listing_id] = {
                    'listing': result['listing'],
                    'vector_score': 0,
                    'text_score': result['score'],
                    'final_score': result['score']
                }
            else:
                combined[listing_id]['text_score'] = result['score']
        
        # Calculate final combined score
        for item in combined.values():
            # Weighted combination of vector and text scores
            item['final_score'] = (
                0.6 * item['vector_score'] + 
                0.4 * item['text_score']
            )
        
        # Sort by final score
        return sorted(
            combined.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )
    
    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Apply additional filters to search results"""
        filtered = []
        
        for result in results:
            listing = result['listing']
            
            # Category filter
            if category and listing.category.slug != category:
                continue
            
            # Location filter
            if location:
                location_lower = location.lower()
                if location_lower not in listing.city.lower() and \
                   location_lower not in listing.county.lower():
                    continue
            
            # Price filters
            if min_price is not None and (listing.price is None or listing.price < min_price):
                continue
            if max_price is not None and (listing.price is None or listing.price > max_price):
                continue
            
            # Geospatial filter
            if latitude and longitude and radius_km:
                if listing.has_coordinates:
                    distance = listing.distance_to_point(latitude, longitude)
                    if distance is None or distance > radius_km:
                        continue
            
            filtered.append(result)
        
        return filtered
    
    def get_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions based on popular searches"""
        try:
            # Get recent searches
            recent_searches = Listing.objects.filter(
                title__icontains=query,
                status='active'
            ).values_list('title', flat=True)[:5]
            
            # Generate suggestions
            suggestions = []
            for title in recent_searches:
                if query.lower() in title.lower():
                    suggestions.append(title)
            
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
            return []
    
    def get_similar_listings(self, listing: Listing, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar listings based on content similarity"""
        try:
            # Get embedding for the reference listing
            try:
                embedding = ListingEmbedding.objects.get(listing=listing)
                reference_vector = embedding.combined_embedding
            except ListingEmbedding.DoesNotExist:
                # Create embedding if it doesn't exist
                text = f"{listing.title} {listing.description}"
                reference_vector = self.encode_text(text)
            
            # Find similar listings
            similar = ListingEmbedding.objects.annotate(
                similarity=1 - CosineDistance('combined_embedding', reference_vector)
            ).filter(
                similarity__gt=0.4
            ).exclude(
                listing=listing
            ).order_by('-similarity')[:limit]
            
            return [
                {
                    'listing': embedding.listing,
                    'similarity_score': float(getattr(embedding, 'similarity', 0.0))
                }
                for embedding in similar
            ]
            
        except Exception as e:
            logger.error(f"Similar listings error: {e}")
            return []

# Global instance
search_engine = EnhancedSemanticSearch()
