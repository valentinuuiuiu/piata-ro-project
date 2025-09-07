from django.db import migrations
from django.contrib.postgres.operations import CreateExtension

class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0013_remove_clerk_user_id'),
    ]

    operations = [
        CreateExtension('vector'),
    ]
