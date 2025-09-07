from django.db import migrations, models
from pgvector.django import VectorField

def generate_embeddings(apps, schema_editor):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        # If the library is not installed, we can't generate embeddings.
        # This is not ideal, but it's better than crashing the migration.
        print("\nWARNING: sentence-transformers is not installed. Skipping embedding generation.")
        print("Please install it with: pip install sentence-transformers")
        return

    Category = apps.get_model('marketplace', 'Category')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    for category in Category.objects.all():
        category.embedding = model.encode(category.name)
        category.save()

class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0015_add_location_point_to_listing'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='embedding',
            field=VectorField(dimensions=384, blank=True, null=True),
        ),
        migrations.RunPython(generate_embeddings),
    ]

