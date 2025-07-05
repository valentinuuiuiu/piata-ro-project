


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from marketplace.models import Favorite, ViewHistory
import redis

User = get_user_model()
r = redis.Redis(host='localhost', port=6379, db=0)

class UserBehaviorCollector:
    """Tracks and stores user behavior for recommendations"""
    
    @staticmethod
    @receiver(post_save, sender=Favorite)
    def track_favorite(sender, instance, created, **kwargs):
        if created:
            r.zincrby(f'user:{instance.user.id}:interactions', 1, instance.listing.id)
            
    @staticmethod        
    @receiver(post_delete, sender=Favorite)
    def track_unfavorite(sender, instance, **kwargs):
        r.zincrby(f'user:{instance.user.id}:interactions', -1, instance.listing.id)
        
    @staticmethod
    @receiver(post_save, sender=ViewHistory) 
    def track_view(sender, instance, created, **kwargs):
        if created:
            r.zincrby(f'user:{instance.user.id}:interactions', 0.5, instance.listing.id)


