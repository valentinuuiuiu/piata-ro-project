
from abc import ABC, abstractmethod
from typing import List
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseRecommender(ABC):
    """Abstract base class for recommendation engines"""
    
    @abstractmethod
    def recommend_for_user(self, user: User, limit: int = 5) -> List[dict]:
        """Generate recommendations for specific user"""
        pass
        
    @abstractmethod  
    def similar_items(self, listing_id: int, limit: int = 5) -> List[dict]:
        """Find similar listings to specified item"""
        pass

    @abstractmethod
    def train_model(self):
        """Retrain recommendation model"""
        pass
