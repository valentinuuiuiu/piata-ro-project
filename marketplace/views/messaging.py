

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Message

@login_required
def messages_view(request):
    """View for displaying user messages"""
    messages = Message.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('-created_at')
    return render(request, 'marketplace/messages.html', {
        'messages': messages
    })

@login_required
def conversation_view(request, user_id):
    """View for a conversation thread"""
    messages = Message.objects.filter(
        sender_id__in=[request.user.id, user_id],
        recipient_id__in=[request.user.id, user_id]
    ).select_related('sender').order_by('created_at')
    return render(request, 'marketplace/conversation.html', {
        'messages': messages,
        'other_user_id': user_id
    })

@login_required
def send_message_view(request, listing_id):
    """View for sending a new message"""
    from ..forms import MessageForm
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.listing_id = listing_id
            message.save()
            return redirect('messages')
    else:
        form = MessageForm()
    
    return render(request, 'marketplace/send_message.html', {
        'form': form,
        'listing_id': listing_id
    })

@login_required
def floating_chat_view(request):
    """View for floating chat widget"""
    return render(request, 'marketplace/messaging/floating_chat.html')

