"""
Blog URLs for Piata.ro marketplace
"""

from django.urls import path
from .views import blog

app_name = 'blog'

urlpatterns = [
    # Blog homepage
    path('', blog.blog_home, name='home'),

    # Individual blog posts
    path('<slug:slug>/', blog.blog_post_detail, name='post_detail'),

    # Category pages
    path('categorie/<slug:slug>/', blog.blog_category, name='category_detail'),

    # Blog search
    path('cautare/', blog.blog_search, name='search'),

    # AJAX endpoints
    path('<int:post_id>/likes/', blog.toggle_blog_like, name='toggle_like'),
    path('<int:post_id>/comentarii/', blog.add_blog_comment, name='add_comment'),
    path('creeaza/', blog.generate_blog_content, name='generate_content'),
    path('status/<int:generator_id>/', blog.ai_content_status, name='content_status'),
    path('newsletter/', blog.subscribe_newsletter, name='newsletter'),

    # RSS/Sitemaps
    path('sitemap.xml', blog.sitemap_blog_posts, name='sitemap'),
    path('rss/', blog.blog_rss, name='rss'),
]
