from django.apps import AppConfig

class MarketplaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'marketplace'
    
    def ready(self):
        # Start auto-repost service when Django starts
        try:
            from .auto_repost_service import auto_repost_service
            auto_repost_service.start()
        except Exception as e:
            print(f"Failed to start auto-repost service: {e}")