import json
import asyncio
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import path
from .models import Conversation, Message
from .mcp_orchestrator import MCPOrchestrator

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
            messages = active_conversation.messages.all()
        except Conversation.DoesNotExist:
            pass
    
    context = {
        'title': 'AI Assistant - Piața.ro',
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'has_permission': True,
        'mcp_status': {'django_sql': 'Online', 'advertising': 'Online', 'stock': 'Online'},  # Simple status for now
    }
    
    return render(request, 'admin/ai_assistant/chat.html', context)

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
            role='user',
            content=message
        )
        
        # Get conversation history
        history = []
        for msg in conversation.messages.filter(timestamp__lt=user_message.timestamp):
            history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Process with MCP Orchestrator
        orchestrator = MCPOrchestrator()
        
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
            role='assistant',
            content=result['response'],
            mcp_tools_used=result.get('tools_used', [])
        )
        
        return JsonResponse({
            'success': True,
            'response': result['response'],
            'conversation_id': conversation.id,
            'message_id': assistant_message.id,
            'tools_used': result.get('tools_used', [])
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
def new_conversation(request):
    """Start a new conversation"""
    conversation = Conversation.objects.create(
        user=request.user,
        title="New Conversation"
    )
    return redirect(f'/ai-assistant/?conversation={conversation.id}')

@staff_member_required 
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()
    except Conversation.DoesNotExist:
        pass
    return redirect('/ai-assistant/')

def ai_status(request):
    """Simple status endpoint for AI assistant"""
    return JsonResponse({'status': 'ok', 'service': 'ai_assistant'})

# Admin integration
class AIAssistantAdmin:
    """Custom admin section for AI Assistant"""
    
    def get_urls(self):
        urls = [
            path('ai-assistant/', ai_assistant_view, name='ai_assistant'),
            path('ai-assistant/chat/', ai_chat_api, name='ai_chat_api'),
            path('ai-assistant/new/', new_conversation, name='new_conversation'),
            path('ai-assistant/delete/<int:conversation_id>/', delete_conversation, name='delete_conversation'),
        ]
        return urls
