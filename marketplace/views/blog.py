"""
Blog Views for Piata.ro
Handles all blog-related functionality including AI-generated content
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages


from marketplace.models_blog import (
    BlogPost, BlogCategory, BlogComment,
    BlogPostLike, AIBlogContentGenerator
)


def blog_home(request):
    """Blog homepage with latest posts"""
    # Get featured posts
    featured_posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).order_by('-views')[:3]

    # Get latest posts
    latest_posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).order_by('-published_at')[:12]

    # Get popular categories
    popular_categories = BlogCategory.objects.annotate(
        post_count=Count('posts')
    ).filter(post_count__gt=0).order_by('-post_count')[:6]

    return render(request, 'marketplace/blog_home.html', {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'popular_categories': popular_categories,
        'page_title': 'Blog Piața.ro - Ghiduri și Ponturi Marketplace'
    })


def blog_post_detail(request, slug):
    """Blog post detail page"""
    post = get_object_or_404(
        BlogPost.objects.select_related('author').prefetch_related('categories'),
        slug=slug,
        status='published',
        published_at__lte=timezone.now()
    )

    # Increment view count
    post.increment_views()

    # Get related posts from same category
    related_posts = BlogPost.objects.filter(
        categories__in=post.categories.all(),
        status='published',
        published_at__lte=timezone.now()
    ).exclude(id=post.id).distinct()[:4]

    # Get comments
    comments = post.comments.filter(
        is_approved=True,
        parent__isnull=True
    ).select_related('author').order_by('-created_at')

    # Check if user liked post
    user_liked = False
    if request.user.is_authenticated:
        user_liked = post.likes.filter(user=request.user).exists()

    return render(request, 'marketplace/blog_post_detail.html', {
        'post': post,
        'related_posts': related_posts,
        'comments': comments,
        'user_liked': user_liked,
        'reading_time': post.get_reading_time()
    })


def blog_category(request, slug):
    """Blog posts by category"""
    category = get_object_or_404(BlogCategory, slug=slug)

    posts = BlogPost.objects.filter(
        categories=category,
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author').order_by('-published_at')

    # Pagination
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'marketplace/blog_category.html', {
        'category': category,
        'posts': page_obj,
        'page_title': f'{category.name} - Blog Piața.ro'
    })


def blog_search(request):
    """Search blog posts"""
    query = request.GET.get('q', '').strip()

    if not query:
        return render(request, 'marketplace/blog_search.html', {
            'posts': [],
            'query': query
        })

    posts = BlogPost.objects.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(excerpt__icontains=query),
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author').order_by('-published_at')

    # Pagination
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'marketplace/blog_search.html', {
        'posts': page_obj,
        'query': query,
        'total_results': posts.count()
    })


@login_required
def toggle_blog_like(request, post_id):
    """AJAX endpoint to toggle like on blog post"""
    if not request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    post = get_object_or_404(BlogPost, id=post_id)
    like, created = BlogPostLike.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        # User already liked, remove the like
        like.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save()
        liked = False
    else:
        # New like
        post.likes_count += 1
        post.save()
        liked = True

    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': post.likes_count
    })


@login_required
def add_blog_comment(request, post_id):
    """AJAX endpoint to add comment to blog post"""
    if not request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    post = get_object_or_404(BlogPost, id=post_id)
    content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'success': False, 'error': 'Comment cannot be empty'})

    if len(content) > 1000:
        return JsonResponse({'success': False, 'error': 'Comment too long'})

    comment = BlogComment.objects.create(
        post=post,
        author=request.user,
        content=content
    )

    # Update post comment count
    post.comments_count += 1
    post.save()

    return JsonResponse({
        'success': True,
        'comment_id': comment.id,
        'author': request.user.username,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
    })


@login_required
def generate_blog_content(request):
    """Admin endpoint to generate AI content"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Not authorized'})

    if not request.method == 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    topic = request.POST.get('topic')
    category_id = request.POST.get('category_id')

    if not topic or not category_id:
        return JsonResponse({'success': False, 'error': 'Missing required fields'})

    try:
        category = BlogCategory.objects.get(id=category_id)

        # Create AI generation task
        generator = AIBlogContentGenerator.objects.create(
            topic=topic,
            category=category,
            target_audience='general',
            keywords=['piața.ro', 'marketplace', category.slug, topic.lower()],
            prompt_used=f"Generate Romanian marketplace blog content for: {topic}"
        )

        # Return tracking ID for later status updates
        return JsonResponse({
            'success': True,
            'generator_id': generator.id,
            'message': 'Content generation started'
        })

    except BlogCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def ai_content_status(request, generator_id):
    """Check AI content generation status"""
    try:
        generator = get_object_or_404(AIBlogContentGenerator, id=generator_id)

        return JsonResponse({
            'status': generator.get_status_display(),
            'progress': generator.status,
            'success': generator.status == 'completed',
            'error': generator.error_message if generator.status == 'failed' else None
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def sitemap_blog_posts(request):
    """XML sitemap for blog posts"""
    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).order_by('-published_at')

    return render(request, 'marketplace/blog_sitemap.xml', {
        'posts': posts
    }, content_type='application/xml')


# RSS Feed functionality
def blog_rss(request):
    """RSS feed for blog posts"""
    posts = BlogPost.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author').order_by('-published_at')[:20]

    return render(request, 'marketplace/blog_rss.xml', {
        'posts': posts,
        'build_date': timezone.now()
    }, content_type='application/rss+xml')


# Email newsletter functionality
@login_required
def subscribe_newsletter(request):
    """Subscribe to blog newsletter"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    email = request.POST.get('email', request.user.email)
    interests = request.POST.getlist('interests[]', [])

    # This would integrate with your email service
    # For now, just confirm subscription
    return JsonResponse({
        'success': True,
        'message': 'Successfully subscribed to newsletter'
    })
