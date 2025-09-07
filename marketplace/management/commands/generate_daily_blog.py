import random
from django.core.management.base import BaseCommand
from mcp_agents.blog_agent.main import generate_blog_post

class Command(BaseCommand):
    help = 'Generates a new blog post on a random topic.'

    def handle(self, *args, **options):
        # List of potential topics for the blog
        topics = [
            "Latest Trends in Romanian E-commerce",
            "How to Find the Best Deals on Piata.ro",
            "A Guide to Second-Hand Shopping in Bucharest",
            "The Rise of Sustainable Fashion in Romania",
            "Top 5 Electronics to Buy Used",
            "Navigating the Real Estate Market in Cluj-Napoca",
            "Tips for Selling Your Car Online",
            "The Future of Online Marketplaces",
            "DIY Home Decor Ideas with Items from Piata.ro",
            "How AI is Changing Online Shopping"
        ]

        # Choose a random topic
        topic = random.choice(topics)

        self.stdout.write(self.style.SUCCESS(f"Attempting to generate a blog post about: '{topic}'"))
        
        post = generate_blog_post(topic=topic)

        if post:
            self.stdout.write(self.style.SUCCESS(f"Successfully created blog post with ID: {post.id} and title: '{post.title}'"))
        else:
            self.stdout.write(self.style.ERROR("Failed to create the blog post."))
