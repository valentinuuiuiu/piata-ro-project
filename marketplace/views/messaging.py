from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.db.models import Q, Max, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from ..models import Message, Listing
from django.db.models import Q, Max, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..models import Message, Listing

User = get_user_model()

def _other_user_id(me_id, s_id, r_id):
    return s_id if r_id == me_id else r_id

@login_required
def messages_view(request):
    me = request.user
    pairs = Message.objects.filter(Q(sender=me) | Q(receiver=me)) \
        .values('sender_id', 'receiver_id') \
        .annotate(last_msg_at=Max('created_at')) \
        .order_by('-last_msg_at')

    summaries = {}
    for p in pairs:
        other_id = _other_user_id(me.id, p['sender_id'], p['receiver_id'])
        if other_id in summaries:
            continue
        last_msg = Message.objects.filter(
            Q(sender_id=me.id, receiver_id=other_id) | Q(sender_id=other_id, receiver_id=me.id)
        ).order_by('-created_at').select_related('sender', 'receiver', 'listing').first()
        if not last_msg:
            continue
        unread = Message.objects.filter(sender_id=other_id, receiver_id=me.id,
is_read=False).count()
        summaries[other_id] = {
            'other_user': User.objects.get(id=other_id),
            'last_message': last_msg,
            'unread_count': unread,
        }

    conversations = list(summaries.values())
    return render(request, 'marketplace/messages.html', {'conversations': conversations})

@login_required
def conversation_view(request, user_id):
    me = request.user
    other = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        content = (request.POST.get('content') or '').strip()
        listing_id = request.POST.get('listing_id')
        if not content:
            return JsonResponse({'success': False, 'error': 'empty'}, status=400)
        listing = None
        if listing_id:
            listing = get_object_or_404(Listing, id=listing_id)
        msg = Message.objects.create(sender=me, receiver=other, listing=listing, content=content)
        return JsonResponse({'success': True, 'created_at':
timezone.localtime(msg.created_at).strftime('%Y-%m-%d %H:%M')})

    thread = Message.objects.filter(
        Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
    ).order_by('created_at').select_related('sender', 'receiver', 'listing')

    Message.objects.filter(sender=other, receiver=me, is_read=False).update(is_read=True)

    return render(request, 'marketplace/conversation.html', {
        'messages': thread,
        'other_user_id': other.id,
        'other_user': other,
    })

@login_required
def send_message_view(request, listing_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    me = request.user
    other_id = request.POST.get('other_user_id')
    content = (request.POST.get('content') or '').strip()
    if not other_id or not content:
        return redirect('marketplace:messages')
    other = get_object_or_404(User, id=other_id)
    listing = get_object_or_404(Listing, id=listing_id)
    Message.objects.create(sender=me, receiver=other, listing=listing, content=content)
    return redirect('marketplace:conversation', user_id=other.id)

def floating_chat_view(request):
    """Render the floating chat widget with local agent configuration."""
    context = {
        'agent_endpoint': 'http://localhost:8001/chat',  # Local MCP agent endpoint
    }
    return render(request, 'floating_chat.html', context)
