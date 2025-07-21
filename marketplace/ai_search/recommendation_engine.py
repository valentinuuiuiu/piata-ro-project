"""
AI-Powered Recommendation Engine for Piata.ro Marketplace
Provides personalized recommendations based on user behavior and content similarity
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Count, Avg, Q
from django.contrib.auth.models import User
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd
from datetime import datetime, timedelta
import logging

from marketplace.models import Listing, UserProfile, Category
from marketplace.models_vector import ListingEmbedding
from .enhanced_search import search_engine

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Advanced recommendation system providing:
    - Collaborative filtering
    - Content-based filtering
    - Hybrid recommendations
    - Trending items
    - Similar items
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def get_personalized_recommendations(
        self,
        user: User,
        limit: int = 10,
        exclude_viewed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations for a user
        Combines collaborative and content-based filtering
        """
        try:
            # Get user's interaction history
            user_interactions = self._get_user_interactions(user)
            
            # Get content-based recommendations
            content_recs = self._content_based_recommendations(user, limit * 2)
            
            # Get collaborative filtering recommendations
            collab_recs = self._collaborative_filtering(user, limit * 2)
            
            # Combine and rank
            combined_recs = self._combine_recommendations(
                content_recs, 
                collab_recs, 
                user_interactions
            )
            
            # Filter out viewed items if requested
            if exclude_viewed:
                viewed_ids = [i['listing'].id for i in user_interactions]
                combined_recs = [r for r in combined_recs if r['listing'].id not in viewed_ids]
            
            return combined_recs[:limit]
            
        except Exception as e:
            logger.error(f"Personalized recommendations error: {e}")
            return []
    
    def get_similar_items(
        self,
        listing: Listing,
        user: Optional[User] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar items based on content and user preferences
        """
        try:
            # Get content-based similar items
            content_similar = search_engine.get_similar_listings(listing, limit * 2)
            
            # Filter by user preferences if user provided
            if user:
                user_profile = UserProfile.objects.get(user=user)
                preferences = self._get_user_preferences(user)
                
                # Filter similar items based on user preferences
                filtered_similar = []
                for item in content_similar:
                    listing = item['listing']
                    preference_score = self._calculate_preference_score(
                        listing, 
                        preferences
                    )
                    if preference_score > 0.3:
                        item['preference_score'] = preference_score
                        filtered_similar.append(item)
                
                content_similar = filtered_similar
            
            # Sort by similarity and return top items
            content_similar.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            return content_similar[:limit]
            
        except Exception as e:
            logger.error(f"Similar items error: {e}")
            return []
    
    def get_trending_items(
        self,
        category: Optional[str] = None,
        location: Optional[str] = None,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending items based on recent activity
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Base queryset
            listings = Listing.objects.filter(
                created_at__gte=start_date,
                status='active'
            )
            
            # Apply category filter
            if category:
                listings = listings.filter(category__slug=category)
            
            # Apply location filter
            if location:
                listings = listings.filter(
                    Q(city__icontains=location) | 
                    Q(county__icontains=location)
                )
            
            # Calculate trending score based on views, likes, and recent creation
            trending_listings = listings.annotate(
                view_count=Count('listing_views'),
                like_count=Count('likes'),
                recent_score=F('created_at')
            ).order_by('-view_count', '-like_count', '-created_at')[:limit]
            
            return [
                {
                    'listing': listing,
                    'trending_score': (
                        listing.view_count * 0.4 + 
                        listing.like_count * 0.6
                    ),
                    'reason': 'trending'
                }
                for listing in trending_listings
            ]
            
        except Exception as e:
            logger.error(f"Trending items error: {e}")
            return []
    
    def get_price_recommendations(
        self,
        listing: Listing
    ) -> Dict[str, Any]:
        """
        Provide price recommendations based on market analysis
        """
        try:
            # Get similar items
            similar_items = Listing.objects.filter(
                category=listing.category,
                status='active'
            ).exclude(id=listing.id)
            
            if listing.price:
                similar_items = similar_items.filter(
                    price__gte=listing.price * 0.5,
                    price__lte=listing.price * 2.0
                )
            
            # Calculate price statistics
            price_stats = similar_items.aggregate(
                avg_price=Avg('price'),
                min_price=Avg('price'),
                max_price=Avg('price'),
                count=Count('id')
            )
            
            # Get market trend
            recent_items = Listing.objects.filter(
                category=listing.category,
                created_at__gte=datetime.now() - timedelta(days=30)
            )
            
            market_trend = recent_items.aggregate(
                avg_price_recent=Avg('price')
            )
            
            # Generate recommendations
            recommendations = {
                'current_price': listing.price,
                'market_average': price_stats['avg_price'],
                'market_range': {
                    'min': price_stats['min_price'],
                    'max': price_stats['max_price']
                },
                'market_trend': market_trend['avg_price_recent'],
                'competitive_price': self._calculate_competitive_price(
                    listing, 
                    price_stats
                ),
                'price_suggestions': self._generate_price_suggestions(
                    listing,
                    price_stats
                )
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Price recommendations error: {e}")
            return {}
    
    def _get_user_interactions(self, user: User) -> List[Dict[str, Any]]:
        """Get user's interaction history"""
        try:
            # Get user's viewed listings
            viewed_listings = user.listing_views.all()
            
            # Get user's liked listings
            liked_listings = user.liked_listings.all()
            
            # Get user's search history
            search_history = user.search_history.all()
            
            interactions = []
            
            # Add viewed listings
            for view in viewed_listings:
                interactions.append({
                    'listing': view.listing,
                    'type': 'view',
                    'timestamp': view.viewed_at
                })
            
            # Add liked listings
            for like in liked_listings:
                interactions.append({
                    'listing': like.listing,
                    'type': 'like',
                    'timestamp': like.created_at
                })
            
            return interactions
            
        except Exception as e:
            logger.error(f"User interactions error: {e}")
            return []
    
    def _content_based_recommendations(
        self,
        user: User,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate content-based recommendations"""
        try:
            # Get user's preferences
            preferences = self._get_user_preferences(user)
            
            # Get active listings
            listings = Listing.objects.filter(status='active')
            
            # Calculate content similarity scores
            recommendations = []
            
            for listing in listings:
                # Get listing embedding
                try:
                    embedding = ListingEmbedding.objects.get(listing=listing)
                    listing_vector = embedding.combined_embedding
                except ListingEmbedding.DoesNotExist:
                    continue
                
                # Calculate preference score
                preference_score = self._calculate_preference_score(
                    listing, 
                    preferences
                )
                
                if preference_score > 0.2:
                    recommendations.append({
                        'listing': listing,
                        'score': preference_score,
                        'type': 'content_based'
                    })
            
            # Sort by score
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Content-based recommendations error: {e}")
            return []
    
    def _collaborative_filtering(
        self,
        user: User,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Generate collaborative filtering recommendations"""
        try:
            # Get user-item matrix
            user_item_matrix = self._build_user_item_matrix()
            
            # Find similar users
            similar_users = self._find_similar_users(user, user_item_matrix)
            
            # Get recommendations from similar users
            recommendations = []
            
            for similar_user, similarity_score in similar_users:
                # Get items liked by similar user but not by current user
                similar_user_likes = similar_user.liked_listings.all()
                
                for like in similar_user_likes:
                    listing = like.listing
                    
                    # Check if current user hasn't interacted with this item
                    if not user.listing_views.filter(listing=listing).exists():
                        recommendations.append({
                            'listing': listing,
                            'score': similarity_score,
                            'type': 'collaborative'
                        })
            
            # Remove duplicates and sort
            unique_recommendations = {}
            for rec in recommendations:
                listing_id = rec['listing'].id
                if listing_id not in unique_recommendations:
                    unique_recommendations[listing_id] = rec
            
            return list(unique_recommendations.values())[:limit]
            
        except Exception as e:
            logger.error(f"Collaborative filtering error: {e}")
            return []
    
    def _get_user_preferences(self, user: User) -> Dict[str, Any]:
        """Extract user preferences from interaction history"""
        try:
            interactions = self._get_user_interactions(user)
            
            # Analyze categories
            category_counts = {}
            for interaction in interactions:
                category = interaction['listing'].category.name
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Analyze price preferences
            prices = [i['listing'].price for i in interactions if i['listing'].price]
            avg_price = np.mean(prices) if prices else None
            
            # Analyze location preferences
            locations = [i['listing'].city for i in interactions if i['listing'].city]
            location_counts = {}
            for location in locations:
                location_counts[location] = location_counts.get(location, 0) + 1
            
            return {
                'categories': category_counts,
                'avg_price': avg_price,
                'locations': location_counts,
                'interaction_count': len(interactions)
            }
            
        except Exception as e:
            logger.error(f"User preferences error: {e}")
            return {}
    
    def _calculate_preference_score(
        self,
        listing: Listing,
        preferences: Dict[str, Any]
    ) -> float:
        """Calculate how well a listing matches user preferences"""
        try:
            score = 0.0
            
            # Category preference
            if listing.category.name in preferences.get('categories', {}):
                category_score = preferences['categories'][listing.category.name]
                score += category_score * 0.4
            
            # Price preference
            avg_price = preferences.get('avg_price')
            if avg_price and listing.price:
                price_diff = abs(listing.price - avg_price) / avg_price
                price_score = max(0, 1 - price_diff)
                score += price_score * 0.3
            
            # Location preference
            if listing.city in preferences.get('locations', {}):
                location_score = preferences['locations'][listing.city]
                score += location_score * 0.2
            
            # Recency bonus
            days_old = (datetime.now().date() - listing.created_at.date()).days
            recency_score = max(0, 1 - days_old / 30)
            score += recency_score * 0.1
            
            return score
            
        except Exception as e:
            logger.error(f"Preference score calculation error: {e}")
            return 0.0
    
    def _build_user_item_matrix(self) -> pd.DataFrame:
        """Build user-item interaction matrix"""
        try:
            # Get all users and listings
            users = User.objects.all()
            listings = Listing.objects.filter(status='active')
            
            # Create matrix
            matrix_data = []
            for user in users:
                user_interactions = []
                for listing in listings:
                    # Check if user has interacted with this listing
                    has_viewed = user.listing_views.filter(listing=listing).exists()
                    has_liked = user.liked_listings.filter(listing=listing).exists()
                    
                    interaction = 0
                    if has_viewed:
                        interaction = 1
                    if has_liked:
                        interaction = 2
                    
                    user_interactions.append(interaction)
                
                matrix_data.append(user_interactions)
            
            return pd.DataFrame(matrix_data, index=[u.id for u in users])
            
        except Exception as e:
            logger.error(f"User-item matrix error: {e}")
            return pd.DataFrame()
    
    def _find_similar_users(
        self,
        user: User,
        user_item_matrix: pd.DataFrame
    ) -> List[Tuple[User, float]]:
        """Find users with similar preferences"""
        try:
            if user.id not in user_item_matrix.index:
                return []
            
            # Get user vector
            user_vector = user_item_matrix.loc[user.id].values.reshape(1, -1)
            
            # Calculate similarities
            similarities = []
            for other_user_id in user_item_matrix.index:
                if other_user_id != user.id:
                    other_vector = user_item_matrix.loc[other_user_id].values.reshape(1, -1)
                    similarity = cosine_similarity(user_vector, other_vector)[0][0]
                    
                    if similarity > 0.1:  # Minimum similarity threshold
                        other_user = User.objects.get(id=other_user_id)
                        similarities.append((other_user, similarity))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:10]  # Top 10 similar users
            
        except Exception as e:
            logger.error(f"Similar users error: {e}")
            return []
    
    def _combine_recommendations(
        self,
        content_recs: List[Dict],
        collab_recs: List[Dict],
        user_interactions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Combine different recommendation strategies"""
        combined = {}
        
        # Add content-based recommendations
        for rec in content_recs:
            listing_id = rec['listing'].id
            if listing_id not in combined:
                combined[listing_id] = {
                    'listing': rec['listing'],
                    'content_score': rec['score'],
                    'collab_score': 0,
                    'final_score': rec['score']
                }
            else:
                combined[listing_id]['content_score'] = rec['score']
        
        # Add collaborative filtering recommendations
        for rec in collab_recs:
            listing_id = rec['listing'].id
            if listing_id not in combined:
                combined[listing_id] = {
                    'listing': rec['listing'],
                    'content_score': 0,
                    'collab_score': rec['score'],
                    'final_score': rec['score']
                }
            else:
                combined[listing_id]['collab_score'] = rec['score']
        
        # Calculate final combined score
        for item in combined.values():
            item['final_score'] = (
                0.6 * item['content_score'] + 
                0.4 * item['collab_score']
            )
        
        # Sort by final score
        return sorted(
            combined.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )
    
    def _calculate_competitive_price(
        self,
        listing: Listing,
        price_stats: Dict[str, float]
    ) -> float:
        """Calculate competitive price based on market analysis"""
        try:
            market_avg = price_stats.get('avg_price', listing.price)
            if not market_avg:
                return listing.price
            
            # Adjust based on listing quality
            quality_factor = 1.0
            
            # Consider listing age
            days_old = (datetime.now().date() - listing.created_at.date()).days
            if days_old > 7:
                quality_factor *= 0.95
            
            competitive_price = market_avg * quality_factor
            
            return max(listing.price * 0.8, competitive_price)
            
        except Exception as e:
            logger.error(f"Competitive price calculation error: {e}")
            return listing.price
    
    def _generate_price_suggestions(
        self,
        listing: Listing,
        price_stats: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate multiple price suggestions"""
        try:
            suggestions = []
            
            market_avg = price_stats.get('avg_price', listing.price)
            
            # Quick sale price
            quick_sale = market_avg * 0.85
            suggestions.append({
                'type': 'quick_sale',
                'price': quick_sale,
                'description': 'Preț competitiv pentru vânzare rapidă'
            })
            
            # Market price
            market_price = market_avg
            suggestions.append({
                'type': 'market_price',
                'price': market_price,
                'description': 'Preț de piață standard'
            })
            
            # Premium price
            premium_price = market_avg * 1.15
            suggestions.append({
                'type': 'premium',
                'price': premium_price,
                'description': 'Preț premium pentru articole de calitate superioară'
            })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Price suggestions error: {e}")
            return []

# Global instance
recommendation_engine = RecommendationEngine()
