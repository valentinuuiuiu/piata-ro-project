import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services.chat_service import marketplace_chat_service

@csrf_exempt
@require_http_methods(["POST"])
def deepseek_chat_view(request):
    """Handle DeepSeek API calls for user chatbot"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Use the marketplace chat service
        response = marketplace_chat_service.user_chat(user_message)
        
        if response.success:
            return JsonResponse({
                'response': response.content
            })
        else:
            return JsonResponse({
                'error': response.error or 'Unknown error'
            }, status=500)
                
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)