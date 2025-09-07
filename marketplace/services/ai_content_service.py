"""
AI Content Generation Service for Piata.ro Blog
Handles automated content generation for Romanian marketplace blog posts.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from .chat_service import marketplace_chat_service
from marketplace.models_blog import (
    BlogPost, BlogCategory, AIBlogContentGenerator,
    BlogContentCalendar
)


class AIContentGenerationService:
    """Service for generating AI-powered blog content"""

    def __init__(self):
        self.chat_service = marketplace_chat_service

    async def generate_blog_content(
        self,
        topic: str,
        category: str,
        keywords: List[str] = None,
        target_audience: str = "general",
        tone: str = "professional",
        word_count: int = 1000
    ) -> Dict[str, Any]:
        """Generate comprehensive blog post content using AI"""

        try:
            # Create enhanced prompt for Romanian marketplace
            prompt = self._build_content_prompt(
                topic=topic,
                category=category,
                keywords=keywords or [],
                target_audience=target_audience,
                tone=tone,
                word_count=word_count
            )

            # Generate content using DeepSeek
            response = await self.chat_service.admin_chat_async(
                message=prompt,
                context=f"Generate Romanian marketplace content about {topic} in {category} category"
            )

            if response.success and response.content:
                # Process and structure the generated content
                processed_content = self._process_generated_content(
                    response.content,
                    topic,
                    keywords or []
                )

                return {
                    'success': True,
                    'title': processed_content.get('title', f"{topic} - Ghid Complet 2025"),
                    'content': processed_content.get('content', response.content),
                    'excerpt': processed_content.get('excerpt', processed_content.get('content', '')[:300]),
                    'seo_title': processed_content.get('seo_title', ''),
                    'seo_description': processed_content.get('seo_description', ''),
                    'keywords': keywords or [],
                    'word_count': len(processed_content.get('content', '').split()),
                    'ai_model_used': response.model
                }

            return {
                'success': False,
                'error': response.error or 'Content generation failed',
                'content': response.content if response.content else ''
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"AI Content Generation Error: {str(e)}",
                'content': ''
            }

    def _build_content_prompt(
        self,
        topic: str,
        category: str,
        keywords: List[str],
        target_audience: str,
        tone: str,
        word_count: int
    ) -> str:
        """Build comprehensive prompt for AI content generation"""

        keywords_str = ', '.join(keywords) if keywords else 'relevante pentru piața românească'

        audience_contexts = {
            'general': 'public larg, români interesați de achiziții și vânzări',
            'beginners': 'începători care intră prima dată pe piața de produse',
            'experienced': 'utilizatori experimentați care caută sfaturi avansate',
            'sellers': 'vânzători care vor să își optimizeze listările și vânzările',
            'buyers': 'cumpărători care caută cele mai bune oferte'
        }

        romanıan_categories = {
            'tech': 'tehnologie și electronice',
            'auto': 'autoturisme și moto',
            'home': 'casă și grădină',
            'fashion': 'modă și beauty',
            'services': 'servicii și afaceri',
            'sports': 'sport și timp liber'
        }

        category_name = romanıan_categories.get(category.lower(), category)

        return f"""
Ești un expert content creator pentru Piața.ro, cea mai mare platformă de marketplace din România.

Generează un articol SEO-optimized pe tema: "{topic}"
Categoria: {category_name}
Cuvinte cheie: {keywords_str}

INSTRUCȚIUNI STRICTE:
1. Scrie ÎNTREGIME în limba română
2. Lungime: {word_count} cuvinte (minimum {word_count-200})
3. Ton: {tone} și informativ
4. Public țintă: {audience_contexts.get(target_audience, 'public larg român')}
5. Include statistici reale din România când poți (piața marketplace, prețuri, tendințe)
6. SEO optimizat pentru Google România
7. Folosește H2, H3 pentru structură
8. Include call-to-action către Piața.ro la sfârșit

STRUCTURA articolului:
1. Titlu atrăgător (max 60 caractere)
2. Intro scurt (2-3 paragrafe) cu hook
3. Secțiune principală cu informații valoroase
4. Exemple practice românești
5. Concluzie cu sfaturi practice
6. Call-to-action către Piata.ro

Scrie articolul complet acum.
"""

    def _process_generated_content(
        self,
        raw_content: str,
        topic: str,
        keywords: List[str]
    ) -> Dict[str, str]:
        """Process and structure the AI-generated content"""

        try:
            lines = raw_content.split('\n')
            title = topic

            # Try to extract title from content
            for line in lines[:3]:
                line = line.strip()
                if line and not line.startswith(('#', '**', '-', '*')):
                    title = line
                    break

            # Extract excerpt (first 300 chars)
            content_clean = raw_content.replace('#', '').strip()
            excerpt = content_clean[:300] + '...' if len(content_clean) > 300 else content_clean

            # Generate SEO title and description
            seo_title = f"{title} - Ghid Complet 2025 | Piata.ro"
            if len(seo_title) > 60:
                seo_title = title[:57] + "..."

            seo_description = excerpt[:160]
            if len(seo_description) > 157:
                seo_description = seo_description[:157] + "..."

            return {
                'title': title,
                'content': content_clean,
                'excerpt': excerpt,
                'seo_title': seo_title,
                'seo_description': seo_description
            }

        except Exception as e:
            # Fallback if processing fails
            return {
                'title': topic,
                'content': raw_content,
                'excerpt': raw_content[:300] + '...',
                'seo_title': topic[:60],
                'seo_description': raw_content[:160]
            }

    async def automated_blog_publishing(
        self,
        calendar_item: BlogContentCalendar
    ) -> bool:
        """Automated publishing based on content calendar"""

        try:
            # Get admin user for posting
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                return False

            # Get random topic and category
            topics = calendar_item.topics or [
                "Ghid cumpărături online România 2025",
                "Cum să vinzi pe marketplace românești",
                "Ponturi pentru listări atractive",
                "Tendințe e-commerce în România",
                "Securitatea tranzacțiilor online"
            ]

            categories = list(calendar_item.categories.all())
            if not categories:
                # Create default category if none exists
                default_cat, _ = BlogCategory.objects.get_or_create(
                    name='Marketplace România',
                    defaults={'slug': 'marketplace-romania'}
                )
                categories = [default_cat]

            topic = topics[0] if topics else "Ghid marketplace România 2025"
            category = categories[0] if categories else categories[0]

            # Generate content
            generation_result = await self.generate_blog_content(
                topic=topic,
                category=category.name.lower(),
                keywords=['piața.ro', 'marketplace', 'românia', 'cumpărături'],
                target_audience='general',
                tone='professional',
                word_count=1500
            )

            if not generation_result.get('success'):
                return False

            # Create and publish blog post
            blog_post = BlogPost.objects.create(
                title=generation_result['title'],
                author=admin_user,
                excerpt=generation_result['excerpt'],
                content=generation_result['content'],
                seo_title=generation_result['seo_title'],
                seo_description=generation_result['seo_description'],
                ai_generated=True,
                ai_model_used=generation_result.get('ai_model_used', 'deepseek-chat'),
                content_prompt=f"Automated generation for topic: {topic}",
                status='published'
            )

            # Add category
            blog_post.categories.add(category)

            # Update calendar
            calendar_item.last_published = timezone.now()
            calendar_item.calculate_next_publish()
            calendar_item.save()

            return True

        except Exception as e:
            print(f"Automated publishing failed: {str(e)}")
            return False

    def generate_category_content_ideas(self, category_name: str) -> List[Dict[str, str]]:
        """Generate content ideas for specific categories"""

        category_ideas = {
            'tech': [
                {'title': 'Cele mai bune laptopuri pentru studenți 2025', 'keywords': ['laptop', 'student', 'ieftin']},
                {'title': 'Televizoare 4K sub 3000 RON - Ghid de cumpărare', 'keywords': ['televizor', '4k', 'ieftin']},
                {'title': 'Telefoane recondiționate - Pro și contra', 'keywords': ['telefon', 'reconditionat', 'garanție']},
            ],
            'home': [
                {'title': 'Mobilă pentru apartament București', 'keywords': ['mobile', 'bucuresti', 'apartament']},
                {'title': 'Electrocasnice esențiale începători', 'keywords': ['electrocasnice', 'bucatarie', 'primul casă']},
                {'title': 'Amenajare balcon mic - Idei practice', 'keywords': ['balcon', 'amenajare', 'spațiu mic']},
            ],
            'fashion': [
                {'title': 'Haine de iarnă calitative sub 200 RON', 'keywords': ['haine', 'iarnă', 'ieftin']},
                {'title': 'Încălțăminte pentru birou - Comfort vs Stil', 'keywords': ['incaltaminte', 'birou', 'comfort']},
                {'title': 'Tendințe modă 2025 pentru români', 'keywords': ['tendințe', 'modă', '2025']},
            ]
        }

        return category_ideas.get(category_name.lower(), [])

    def schedule_content_generation(
        self,
        topics: List[str],
        category: BlogCategory,
        audience: str = 'general'
    ) -> List[AIBlogContentGenerator]:
        """Schedule multiple content generation tasks"""

        generated_items = []

        for topic in topics:
            generator = AIBlogContentGenerator.objects.create(
                topic=topic,
                category=category,
                target_audience=audience,
                keywords=['piata.ro', category.slug, topic.lower()],
                word_count_target=1200,
                prompt_used=f"Generate blog content for {topic} in {category.name} category"
            )

            # Start async generation
            asyncio.create_task(self.process_generation(generator))

            generated_items.append(generator)

        return generated_items

    async def process_generation(self, generator: AIBlogContentGenerator):
        """Process a single content generation request"""

        try:
            result = await self.generate_blog_content(
                topic=generator.topic,
                category=generator.category.name.lower(),
                keywords=generator.keywords,
                target_audience=generator.target_audience,
                tone=generator.tone,
                word_count=generator.word_count_target
            )

            if result.get('success'):
                generator.mark_completed(result['content'])

                # Optionally create the blog post
                creator = await self.create_blog_post_from_generation(generator, result)
                return creator
            else:
                generator.mark_failed(result.get('error', 'Generation failed'))

        except Exception as e:
            generator.mark_failed(str(e))

    async def create_blog_post_from_generation(
        self,
        generator: AIBlogContentGenerator,
        generation_result: Dict[str, Any]
    ) -> BlogPost:
        """Create a blog post from successful generation"""

        try:
            # Get admin user
            admin_user = User.objects.filter(is_staff=True).first()

            # Create blog post
            post = BlogPost.objects.create(
                title=generation_result['title'],
                author=admin_user,
                excerpt=generation_result['excerpt'],
                content=generation_result['content'],
                seo_title=generation_result['seo_title'],
                seo_description=generation_result['seo_description'],
                ai_generated=True,
                ai_model_used=generation_result.get('ai_model_used', 'deepseek-chat'),
                content_prompt=generator.prompt_used,
                status='draft'  # Start as draft for review
            )

            # Add category
            post.categories.add(generator.category)

            # Link generation to post
            generator.blog_post = post
            generator.save()

            return post

        except Exception as e:
            print(f"Failed to create blog post: {str(e)}")
            return None


# Global service instance
ai_content_service = AIContentGenerationService()
