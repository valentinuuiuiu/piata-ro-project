"""
Django management command for automated blog content generation
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
import asyncio
from marketplace.models_blog import (
    BlogContentCalendar, BlogPost, BlogCategory
)
from marketplace.services.ai_content_service import ai_content_service


class Command(BaseCommand):
    help = 'Automatically generate and publish blog content based on content calendar'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually generating content'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Specific category to generate content for'
        )
        parser.add_argument(
            '--topic',
            type=str,
            help='Specific topic to generate content for'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        specific_category = options.get('category')
        specific_topic = options.get('topic')

        if specific_topic and specific_category:
            # Generate specific content
            self.stdout.write(f"Generating content for topic: {specific_topic}")
            asyncio.run(self.generate_specific_content(specific_topic, specific_category, dry_run))
        else:
            # Run automated calendar check
            self.stdout.write("Checking content calendar...")
            self.check_and_generate_automated(dry_run)

    async def generate_specific_content(self, topic, category_name, dry_run):
        """Generate content for a specific topic and category"""

        try:
            # Get or create category
            category, created = BlogCategory.objects.get_or_create(
                name=category_name,
                defaults={'slug': category_name.lower().replace(' ', '-')}
            )

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"[DRY RUN] Would generate: '{topic}' in category '{category.name}'")
                )
                return

            # Generate AI content
            self.stdout.write(f"Generating AI content for: {topic}")

            result = await ai_content_service.generate_blog_content(
                topic=topic,
                category=category.name.lower(),
                keywords=['piața.ro', 'marketplace', 'românia', category.name.lower()],
                target_audience='general',
                tone='professional',
                word_count=1200
            )

            if result.get('success'):
                # Create blog post
                admin_user = User.objects.filter(is_staff=True).first()
                if not admin_user:
                    self.stdout.write(
                        self.style.ERROR("No admin user found for blog-posting")
                    )
                    return

                post = BlogPost.objects.create(
                    title=result['title'],
                    author=admin_user,
                    excerpt=result['excerpt'],
                    content=result['content'],
                    seo_title=result['seo_title'],
                    seo_description=result['seo_description'],
                    ai_generated=True,
                    ai_model_used=result.get('ai_model_used', 'deepseek-chat'),
                    content_prompt=f"Automated generation for topic: {topic}",
                    status='published'
                )

                # Add category
                post.categories.add(category)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Generated and published: {post.title} ({len(result['content'])} chars)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error generating content: {str(e)}")
            )

    def check_and_generate_automated(self, dry_run):
        """Check content calendar and generate due content"""

        now = timezone.now()
        due_calendars = BlogContentCalendar.objects.filter(
            is_active=True,
            next_publish__lte=now
        )

        if not due_calendars.exists():
            self.stdout.write("No content due for generation at this time.")
            return

        self.stdout.write(f"Found {due_calendars.count()} calendars ready for generation.")

        for calendar in due_calendars:
            self.stdout.write(f"\n📅 Processing calendar: {calendar.title}")

            if self.process_calendar(calendar, dry_run):
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Successfully processed calendar: {calendar.title}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to process calendar: {calendar.title}")
                )

    def process_calendar(self, calendar, dry_run):
        """Process a single content calendar"""
        try:
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would process calendar: {calendar.title}")
                return True

            # Get a topic from the calendar
            topics = calendar.topics
            if not topics:
                self.stdout.write(self.style.WARNING(f"No topics defined for calendar: {calendar.title}"))
                return False

            topic = topics[0]  # Use first topic for now

            # Get a category
            categories = list(calendar.categories.all())
            if not categories:
                self.stdout.write(self.style.WARNING(f"No categories defined for calendar: {calendar.title}"))
                return False

            category = categories[0]  # Use first category

            # Generate content using asyncio
            asyncio.run(self.generate_calendar_content(calendar, topic, category))

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing calendar: {str(e)}"))
            return False

    async def generate_calendar_content(self, calendar, topic, category):
        """Generate content for a calendar item"""
        try:
            result = await ai_content_service.generate_blog_content(
                topic=topic,
                category=category.name.lower(),
                keywords=['piața.ro', 'marketplace', 'românia', category.name.lower()],
                target_audience='general',
                tone='professional',
                word_count=1200
            )

            if result.get('success'):
                # Create blog post
                admin_user = User.objects.filter(is_staff=True).first()

                post = BlogPost.objects.create(
                    title=result['title'],
                    author=admin_user,
                    excerpt=result['excerpt'],
                    content=result['content'],
                    seo_title=result['seo_title'],
                    seo_description=result['seo_description'],
                    ai_generated=True,
                    ai_model_used=result.get('ai_model_used', 'deepseek-chat'),
                    content_prompt=f"Automated calendar generation for {calendar.title}",
                    status='published'
                )

                # Add category
                post.categories.add(category)

                # Update calendar
                calendar.last_published = timezone.now()
                calendar.calculate_next_publish()
                calendar.save()

                self.stdout.write(
                    self.style.SUCCESS(f"📝 Published: {post.title}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to generate content: {result.get('error')}")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Calendar generation error: {str(e)}")
            )

    def create_default_content_calendars(self):
        """Create some default content calendars for demo purposes"""

        calendars = [
            {
                'title': 'Marketplace Ghiduri Săptămânale',
                'frequency': 'weekly',
                'topics': [
                    'Cum să vinzi mai repede pe Piața.ro',
                    'Securitatea în tranzacțiile online România',
                    'Fotografii profesioniste pentru listări',
                    'Prețuri competitive în piața românească'
                ]
            },
            {
                'title': 'Tendințe E-commerce Lunare',
                'frequency': 'monthly',
                'topics': [
                    'Tendințe marketplace România 2025',
                    'Cum să folosești AI pentru vânzări',
                    'Strategii de marketing online pentru seller-i',
                    'Viitorul e-commerce în România'
                ]
            }
        ]

        # Get or create default category
        category, _ = BlogCategory.objects.get_or_create(
            name='Marketplace România',
            defaults={'slug': 'marketplace-romania'}
        )

        for cal_data in calendars:
            calendar, created = BlogContentCalendar.objects.get_or_create(
                title=cal_data['title'],
                defaults={
                    'frequency': cal_data['frequency'],
                    'topics': cal_data['topics']
                }
            )

            if created:
                calendar.categories.add(category)
                calendar.calculate_next_publish()
                calendar.save()

                self.stdout.write(
                    self.style.SUCCESS(f"Created calendar: {calendar.title}")
                )
