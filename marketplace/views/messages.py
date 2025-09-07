from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max
from django.contrib import messages
from ..models import Message, User, Listing

@login_required
def messages_view(request):
    """Messages page with conversation grouping."""
    if not request.user.is_authenticated:
        return redirect('login')

    # Get conversations - group messages by participants
    conversations = []

    # Get all unique conversation partners
    conversation_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct().exclude(id=request.user.id)

    for other_user in conversation_users:
        # Get latest message in this conversation
        latest_message = Message.objects.filter(
            (Q(sender=request.user, receiver=other_user) |
             Q(sender=other_user, receiver=request.user))
        ).order_by('-created_at').first()

        # Count unread messages from this user
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=request.user,
            is_read=False
        ).count()

        if latest_message:
            conversations.append({
                'other_user': other_user,
                'last_message': latest_message,
                'unread_count': unread_count,
            })

    # Sort conversations by latest message
    conversations.sort(key=lambda x: x['last_message'].created_at, reverse=True)

    context = {
        "conversations": conversations,
        "page_title": "Mesajele mele",
    }

    return render(request, "marketplace/messages.html", context)

@login_required
def conversation_view(request, user_id):
    """View a conversation with a specific user."""
    other_user = get_object_or_404(User, id=user_id)

    # Get all messages between these two users
    messages = Message.objects.filter(
        (Q(sender=request.user, receiver=other_user) |
         Q(sender=other_user, receiver=request.user))
    ).order_by('created_at')

    # Mark messages as read
    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'created_at': message.created_at.strftime('%H:%M'),
                        'sender': message.sender.username
                    }
                })
            return redirect('marketplace:conversation', user_id=user_id)

    context = {
        'other_user': other_user,
        'messages': messages,
        'page_title': f'Conversație cu {other_user.username}',
    }

    return render(request, "marketplace/conversation.html", context)

@login_required
def send_message_view(request, listing_id):
    """Send a message about a specific listing."""
    listing = get_object_or_404(Listing, id=listing_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content and listing.user != request.user:
            message = Message.objects.create(
                sender=request.user,
                receiver=listing.user,
                listing=listing,
                content=content
            )
            messages.success(request, 'Mesajul tău a fost trimis cu succes!')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            return redirect('marketplace:listing_detail', listing_id=listing.id)

    return redirect('marketplace:listing_detail', listing_id=listing.id)
