from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0016_add_embedding_to_category'),
    ]

    operations = [
        # Replace GIS PointField with regular CharField for SQLite
        # Use SeparateDatabaseAndState to avoid calling GIS-specific DB ops
        # (connection.ops.geo_db_type is not available on non-spatial backends)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(
                    model_name='listing',
                    name='location_point',
                ),
                migrations.AddField(
                    model_name='listing',
                    name='location_point',
                    field=models.CharField(max_length=100, blank=True, null=True, help_text='Location coordinates as "lat,lng" string'),
                ),
            ],
        ),
    ]
