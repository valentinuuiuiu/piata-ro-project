import json
import asyncio
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import path
from django.conf import settings
from .models import Conversation, Message, MCPServerConfig, ChatSessionLog
from .smart_mcp_orchestrator import SmartMCPOrchestrator
from marketplace.services.chat_service import marketplace_chat_service

@staff_member_required
def ai_assistant_view(request):
    """Main AI Assistant interface in Django Admin"""
    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')[:10]
    
    # Get active conversation
    conversation_id = request.GET.get('conversation')
    active_conversation = None
    messages = []
    
    if conversation_id:
        try:
            active_conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            messages = Message.objects.filter(conversation=active_conversation)
        except Conversation.DoesNotExist:
            pass
    
    context = {
        'title': 'AI Assistant - Piața.ro',
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'has_permission': True,
        'mcp_status': {'django_sql': 'Online', 'advertising': 'Online', 'stock': 'Online'},  # Simple status for now
        'mcp_orchestrator_endpoint': getattr(settings, 'MCP_ORCHESTRATOR_ENDPOINT', 'http://localhost:8000'),
        'mcp_servers': getattr(settings, 'MCP_SERVERS', {}),
    }
    
    return render(request, 'admin/ai_assistant/chat.html', context)

@staff_member_required
def mcp_orchestrator_view(request):
    """MCP Orchestrator interface in Django Admin"""
    context = {
        'title': 'MCP Orchestrator - Piața.ro',
        'mcp_orchestrator_endpoint': getattr(settings, 'MCP_ORCHESTRATOR_ENDPOINT', 'http://localhost:8000'),
        'mcp_servers': getattr(settings, 'MCP_SERVERS', {}),
    }
    
    return render(request, 'admin/ai_assistant/mcp_orchestrator.html', context)

@csrf_exempt
def ai_chat_api(request):
    """API endpoint for chat with AI assistant"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check authentication manually since we're using csrf_exempt
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            except Conversation.DoesNotExist:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=message[:50] + '...' if len(message) > 50 else message
                )
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title=message[:50] + '...' if len(message) > 50 else message
            )
        
        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            is_user=True,
            text=message
        )
        
        # Get conversation history
        history = []
        for msg in Message.objects.filter(conversation=conversation, timestamp__lt=user_message.timestamp):
            history.append({
                'role': 'user' if msg.is_user else 'assistant',
                'content': msg.text,
            })
        
        # Process with MCP Orchestrator
        orchestrator = SmartMCPOrchestrator()
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                orchestrator.process_request(message, history)
            )
        finally:
            loop.close()
        
        # Save assistant response
        assistant_message = Message.objects.create(
            conversation=conversation,
            is_user=False,
            text=result.response
        )
        
        # Log the chat session
        ChatSessionLog.objects.create(
            user=request.user,
            status='completed'
        )
        
        return JsonResponse({
            'success': True,
            'response': result.response,
            'conversation_id': getattr(conversation, 'id', getattr(conversation, 'pk', None)),
            'message_id': assistant_message.pk,
            'tools_used': getattr(result, 'tools_used', []),
            'intent_analysis': getattr(result.intent_analysis, 'dict', lambda: None)() if result.intent_analysis else None
        })
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Chat API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def new_conversation(request):
    """Start a new conversation"""
    conversation = Conversation.objects.create(
        user=request.user,
        title="New Conversation"
    )
    return JsonResponse({'conversation_id': conversation.pk})

@staff_member_required 
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()
    except Conversation.DoesNotExist:
        pass
    return JsonResponse({'success': True})

def ai_status(request):
    """Simple status endpoint for AI assistant"""
    return JsonResponse({'status': 'ok', 'service': 'ai_assistant'})

@staff_member_required
def check_mcp_server(request, server_name):
    """Check status of specific MCP server"""
    try:
        server_config = getattr(settings, 'MCP_SERVERS', {}).get(server_name)
        if not server_config:
            return JsonResponse({'status': 'offline', 'error': 'Server not configured'})
        
        # Try to connect to the server
        import httpx
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{server_config.url}/health", follow_redirects=True)
            if response.status_code == 200:
                return JsonResponse({'status': 'online'})
            else:
                return JsonResponse({'status': 'offline', 'error': f'Server returned {response.status_code}'})
    except Exception as e:
        return JsonResponse({'status': 'offline', 'error': str(e)})

# Admin integration
class AIAssistantAdmin(admin.ModelAdmin):
    """Custom admin section for AI Assistant"""
    
    def get_urls(self):
        urls = [
            path('ai-assistant/', ai_assistant_view, name='ai_assistant'),
            path('ai-assistant/mcp-orchestrator/', mcp_orchestrator_view, name='mcp_orchestrator'),
            path('ai-assistant/chat/', ai_chat_api, name='ai_chat_api'),
            path('ai-assistant/new/', new_conversation, name='new_conversation'),
            path('ai-assistant/delete/<int:conversation_id>/', delete_conversation, name='delete_conversation'),
            path('ai-assistant/status/', ai_status, name='ai_status'),
            path('ai-assistant/check-mcp/<str:server_name>/', check_mcp_server, name='check_mcp_server'),
        ]
        return urls

# Custom admin integration - handled through URL inclusion in main urls.py
