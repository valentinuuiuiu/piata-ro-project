from django.conf import settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
import django
django.setup()
from marketplace.models import Category

cats = Category.objects.all()
print(f'Total categories: {len(cats)}')
for c in cats:
    parent_name = c.parent.name if c.parent else 'None'
    emb_dim = len(c.embedding) if c.embedding else 0
    print(f'{c.name} | Parent: {parent_name} | Embedding dim: {emb_dim}')
