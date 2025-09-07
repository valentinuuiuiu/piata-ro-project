from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse

try:
    from ckeditor.fields import RichTextField
except ImportError:
    RichTextField = models.TextField  # Fallback if ckeditor not available

try:
    from taggit.managers import TaggableManager
except ImportError:
    # Fallback implementation without taggit
    class TaggableManager:
        def __init__(self, **kwargs):
            pass

try:
    from meta.models import ModelMeta
except ImportError:
    # Fallback for django-meta
    ModelMeta = type('ModelMeta', (), {})

class BlogPost(ModelMeta, models.Model):
    """Blog post model with SEO optimization"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    )

    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.TextField(max_length=300, help_text="Brief summary for meta description and listings")

    # Content fields
    content = RichTextField()
    featured_image = models.ImageField(upload_to='blog/featured/%Y/%m/', blank=True, null=True)

    # Meta information
    tags = TaggableManager()
    categories = models.ManyToManyField('BlogCategory', related_name='posts')

    # SEO fields
    seo_title = models.CharField(max_length=60, blank=True, help_text="Leave empty to use title")
    seo_description = models.TextField(max_length=160, blank=True, help_text="Meta description")

    # Publishing
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(blank=True, null=True)
    scheduled_for = models.DateTimeField(blank=True, null=True)

    # AI Generation
    ai_generated = models.BooleanField(default=False)
    ai_model_used = models.CharField(max_length=50, blank=True)
    content_prompt = models.TextField(blank=True, help_text="The prompt used to generate this content")

    # Performance tracking
    views = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")

    # Social engagement
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['-published_at', 'status']),
            models.Index(fields=['views', 'status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.seo_title and self.title:
            self.seo_title = self.title[:60]

        if not self.seo_description and self.excerpt:
            self.seo_description = self.excerpt[:160]

        # Calculate reading time (approximate)
        words = len(self.content.split()) if self.content else 0
        self.reading_time = max(1, words // 200)  # Assume 200 words per minute

        # Handle publishing
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None

        # Set meta information
        if not self._meta_title:
            self._meta_title = self.seo_title or self.title

        if not self._meta_description:
            self._meta_description = self.seo_description or self.excerpt

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_reading_time(self):
        return f"{self.reading_time} min read"

    def is_published(self):
        return self.status == 'published' and self.published_at <= timezone.now()

    def increment_views(self):
        """Increment view count safely"""
        BlogPost.objects.filter(pk=self.pk).update(views=models.F('views') + 1)
        self.refresh_from_db(fields=['views'])

    @property
    def total_engagement(self):
        """Calculate total social engagement"""
        return self.likes_count + self.comments_count + self.shares_count


class BlogCategory(models.Model):
    """Blog categories for content organization"""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories'
    )

    # SEO and display
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    icon = models.CharField(max_length=50, blank=True)

    # Analytics
    posts_count = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)

    # Colors for theming
    color = models.CharField(max_length=7, default='#007bff')

    class Meta:
        ordering = ['name']
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

    def update_stats(self):
        """Update category statistics"""
        self.posts_count = self.posts.filter(status='published').count()
        self.total_views = self.posts.filter(status='published').aggregate(
            total=models.Sum('views')
        )['total'] or 0
        self.save()


class BlogComment(models.Model):
    """Comments on blog posts"""

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')

    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    content = models.TextField(max_length=1000)

    is_approved = models.BooleanField(default=True)
    is_spam = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Blog Comment"
        verbose_name_plural = "Blog Comments"

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    def get_replies(self):
        """Get all replies to this comment"""
        return BlogComment.objects.filter(parent=self)


class BlogPostLike(models.Model):
    """Likes for blog posts"""

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_likes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('post', 'user')
        verbose_name = "Blog Post Like"
        verbose_name_plural = "Blog Post Likes"

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class BlogNewsletterSubscriber(models.Model):
    """Newsletter subscribers"""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(default=timezone.now)

    # Marketing preferences
    interests = models.JSONField(default=list, help_text="List of interests/tags")

    class Meta:
        ordering = ['-subscribed_at']
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name} <{self.email}>"
        return self.email


class AIBlogContentGenerator(models.Model):
    """Tracks AI content generation for blogs"""

    STATUS_CHOICES = (
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('published', 'Published'),
    )

    topic = models.CharField(max_length=200)
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE)
    target_audience = models.CharField(max_length=50, default='general')

    # Content parameters
    keywords = models.JSONField(default=list)
    word_count_target = models.PositiveIntegerField(default=1000)
    tone = models.CharField(max_length=50, default='professional')

    # AI Generation details
    prompt_used = models.TextField()
    ai_model = models.CharField(max_length=50, default='deepseek-chat')
    generated_content = models.TextField(blank=True)

    # Status tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='generating')
    error_message = models.TextField(blank=True)

    # Timestamps
    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)

    # Output (if successful)
    blog_post = models.OneToOneField(
        BlogPost,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='ai_generation'
    )

    class Meta:
        ordering = ['-requested_at']
        verbose_name = "AI Blog Content Generator"
        verbose_name_plural = "AI Blog Content Generators"

    def __str__(self):
        return f"AI Generation: {self.topic} ({self.status})"

    def mark_completed(self, content):
        """Mark generation as completed with content"""
        self.generated_content = content
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error_msg):
        """Mark generation as failed"""
        self.status = 'failed'
        self.error_message = error_msg
        self.completed_at = timezone.now()
        self.save()


class BlogContentCalendar(models.Model):
    """Content calendar for automated blog publishing"""

    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Content generation settings
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    topics = models.JSONField(default=list, help_text="List of content topics")
    categories = models.ManyToManyField(BlogCategory)

    # Publishing settings
    publish_hour = models.PositiveIntegerField(default=9, help_text="Hour to publish (0-23)")  # 9 AM
    publish_day = models.PositiveIntegerField(default=0, help_text="Day of week (0=Monday, 6=Sunday)")

    # Status
    is_active = models.BooleanField(default=True)
    last_published = models.DateTimeField(blank=True, null=True)
    next_publish = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Content Calendar"
        verbose_name_plural = "Blog Content Calendars"

    def __str__(self):
        return f"{self.title} ({self.frequency})"

    def calculate_next_publish(self):
        """Calculate the next publish date"""
        now = timezone.now()

        if self.frequency == 'daily':
            next_date = now.date() + timedelta(days=1)
            self.next_publish = timezone.datetime.combine(
                next_date,
                timezone.time(hour=self.publish_hour),
                tz=timezone.get_current_timezone()
            )
        elif self.frequency == 'weekly':
            days_ahead = (self.publish_day - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_date = now.date() + timedelta(days=days_ahead)
            self.next_publish = timezone.datetime.combine(
                next_date,
                timezone.time(hour=self.publish_hour),
                tz=timezone.get_current_timezone()
            )
        elif self.frequency == 'biweekly':
            days_ahead = (self.publish_day - now.weekday()) % 14
            if days_ahead == 0:
                days_ahead = 14
            next_date = now.date() + timedelta(days=days_ahead)
            self.next_publish = timezone.datetime.combine(
                next_date,
                timezone.time(hour=self.publish_hour),
                tz=timezone.get_current_timezone()
            )
        elif self.frequency == 'monthly':
            next_month = now.replace(day=1) + timedelta(days=32)
            next_date = next_month.replace(day=1)
            self.next_publish = timezone.datetime.combine(
                next_date,
                timezone.time(hour=self.publish_hour),
                tz=timezone.get_current_timezone()
            )

    def save(self, *args, **kwargs):
        if not self.id or not self.next_publish:
            self.calculate_next_publish()
        super().save(*args, **kwargs)
