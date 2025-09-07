import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from marketplace.models_blog import BlogPost
from django.contrib.auth.models import User
# Assume a function to call a large language model
# from some_llm_service import generate_text 

def generate_blog_post(topic: str, author_username: str = "auto_blogger"):
    """
    Generates and saves a new blog post.
    """
    print(f"Generating blog post on the topic: {topic}")

    # Find or create the author
    author, created = User.objects.get_or_create(username=author_username, defaults={'first_name': 'Auto', 'last_name': 'Blogger'})
    if created:
        print(f"Created new author: {author_username}")

    # --- Placeholder for LLM call ---
    # In a real scenario, you would call your LLM here.
    # For now, we'll use placeholder content.
    # title_prompt = f"Generate a catchy, SEO-friendly title for a blog post about '{topic}'."
    # title = generate_text(title_prompt)
    # excerpt_prompt = f"Generate a 2-sentence meta description for a blog post titled '{title}'."
    # excerpt = generate_text(excerpt_prompt)
    # content_prompt = f"Write a 500-word blog post about '{topic}'. Use markdown for formatting."
    # content = generate_text(content_prompt)
    
    title = f"Exploring {topic}: A Deep Dive"
    excerpt = f"A brief look into the world of {topic}. Discover the key aspects and why it matters in today's landscape."
    content = f"""
## Introduction to {topic}

This is a detailed blog post about {topic}. Here we explore the various facets of this interesting subject.

### Key Point 1
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

### Key Point 2
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

## Conclusion
In summary, {topic} is a field with a lot of potential.
"""
    # --- End of Placeholder ---

    try:
        post = BlogPost.objects.create(
            title=title,
            author=author,
            excerpt=excerpt,
            content=content,
            status='published',  # Or 'draft'
            ai_generated=True,
            ai_model_used="Placeholder-GPT-4",
            content_prompt=f"A blog post about {topic}"
        )
        print(f"Successfully created blog post: '{post.title}' (ID: {post.id})")
        return post
    except Exception as e:
        print(f"Error creating blog post: {e}")
        return None

if __name__ == "__main__":
    # Example usage:
    # This allows running the script directly for testing.
    # In production, this would be called from a management command.
    generate_blog_post(topic="The Future of E-Commerce in Romania")
