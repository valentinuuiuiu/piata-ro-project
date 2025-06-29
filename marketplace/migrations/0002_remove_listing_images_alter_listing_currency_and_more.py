# Generated by Django 4.2.22 on 2025-06-06 18:31

from django.db import migrations, models
import django.db.models.deletion
import marketplace.models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='images',
        ),
        migrations.AlterField(
            model_name='listing',
            name='currency',
            field=models.CharField(choices=[('RON', 'Lei (RON)'), ('EUR', 'Euro (EUR)'), ('USD', 'Dolari (USD)')], default='RON', max_length=3),
        ),
        migrations.CreateModel(
            name='ListingImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=marketplace.models.listing_image_path)),
                ('is_main', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='marketplace.listing')),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
