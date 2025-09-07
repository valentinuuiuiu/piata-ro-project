from django.db import migrations, models
import django.contrib.gis.db.models.fields
from django.contrib.gis.geos import Point

def populate_location_point(apps, schema_editor):
    Listing = apps.get_model('marketplace', 'Listing')
    for listing in Listing.objects.all():
        if listing.longitude is not None and listing.latitude is not None:
            listing.location_point = Point(float(listing.longitude), float(listing.latitude))
            listing.save()

class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0014_enable_pgvector'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='location_point',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.RunPython(populate_location_point),
    ]
