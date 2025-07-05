


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .services import CollaborativeFilteringRecommender

User = get_user_model()
recommender = CollaborativeFilteringRecommender()

@api_view(['GET'])
def user_recommendations(request, user_id):
    """Get personalized recommendations for user"""
    try:
        user = User.objects.get(pk=user_id)
        recommendations = recommender.recommend_for_user(user)
        return Response(recommendations)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def similar_listings(request, listing_id):
    """Get similar listings to specified item"""
    similar = recommender.similar_items(listing_id)
    return Response(similar)


