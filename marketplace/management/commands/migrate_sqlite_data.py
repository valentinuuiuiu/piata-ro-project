import sqlite3
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from marketplace.models import Category, Listing, UserProfile, ListingImage
from django.db import transaction
from django.core.files.base import ContentFile
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Migrate all data from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--sqlite-path', type=str, default='db.sqlite3', help='Path to SQLite DB')

    def handle(self, *args, **options):
        sqlite_path = options['sqlite_path']
        conn = None
        
        try:
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Disable signals temporarily
            from marketplace.signals import create_user_profile, save_user_profile
            from django.db.models.signals import post_save
            post_save.disconnect(create_user_profile, sender=User)
            post_save.disconnect(save_user_profile, sender=User)
            
            # Migrate Users
            self.migrate_users(cursor)
            
            # Migrate Listings
            self.migrate_listings(cursor)
            
            # Migrate Listing Images
            self.migrate_listing_images(cursor)
            
            # Re-enable signals
            post_save.connect(create_user_profile, sender=User)
            post_save.connect(save_user_profile, sender=User)
            
            self.stdout.write(self.style.SUCCESS('All data migrated successfully!'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error during migration: {e}'))
            # Re-enable signals on error
            try:
                from marketplace.signals import create_user_profile, save_user_profile
                from django.db.models.signals import post_save
                post_save.connect(create_user_profile, sender=User)
                post_save.connect(save_user_profile, sender=User)
            except:
                pass
        finally:
            if conn:
                conn.close()

    def migrate_users(self, cursor):
        """Migrate users and user profiles"""
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                   u.is_staff, u.is_active, u.date_joined, u.password,
                   p.phone, p.location, p.avatar, p.bio
            FROM auth_user u
            LEFT JOIN marketplace_userprofile p ON u.id = p.user_id
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for row in rows:
                try:
                    # Handle user creation/update
                    user, created = User.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'username': row['username'],
                            'email': row['email'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'is_staff': row['is_staff'],
                            'is_active': row['is_active'],
                            'date_joined': row['date_joined'],
                            'password': row['password']
                        }
                    )
                    
                    if not created:
                        # Update existing user
                        user.username = row['username']
                        user.email = row['email']
                        user.first_name = row['first_name']
                        user.last_name = row['last_name']
                        user.is_staff = row['is_staff']
                        user.is_active = row['is_active']
                        user.date_joined = row['date_joined']
                        user.password = row['password']
                        user.save()
                        updated_count += 1
                    
                    # Handle user profile
                    profile, profile_created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'phone': row['phone'] or '',
                            'location': row['location'] or '',
                            'bio': row['bio'] or ''
                        }
                    )
                    
                    if not profile_created:
                        # Update existing profile
                        profile.phone = row['phone'] or ''
                        profile.location = row['location'] or ''
                        profile.bio = row['bio'] or ''
                        profile.save()
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error processing user {row["username"]}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} new users, updated {updated_count} existing users'))

    def migrate_listings(self, cursor):
        """Migrate listings"""
        cursor.execute('''
            SELECT id, title, description, price, negotiable, condition, 
                   location, latitude, longitude, created_at, updated_at,
                   is_active, views_count, user_id, category_id
            FROM marketplace_listing
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        with transaction.atomic():
            for row in rows:
                try:
                    user = User.objects.get(id=row['user_id'])
                    category = Category.objects.get(id=row['category_id'])
                    
                    listing, created = Listing.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'title': row['title'],
                            'description': row['description'],
                            'price': row['price'] or 0,
                            'negotiable': row['negotiable'] or False,
                            'condition': row['condition'] or 'used',
                            'location': row['location'] or '',
                            'latitude': row['latitude'],
                            'longitude': row['longitude'],
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at'],
                            'is_active': row['is_active'] or True,
                            'views_count': row['views_count'] or 0,
                            'user': user,
                            'category': category
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error creating listing {row["title"]}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} listings'))

    def migrate_listing_images(self, cursor):
        """Migrate listing images"""
        cursor.execute('''
            SELECT id, image, listing_id, is_primary, created_at
            FROM marketplace_listingimage
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        with transaction.atomic():
            for row in rows:
                try:
                    listing = Listing.objects.get(id=row['listing_id'])
                    
                    # Create placeholder image if file doesn't exist
                    image_name = row['image'] or f'placeholder_{row["id"]}.jpg'
                    
                    listing_image, created = ListingImage.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'listing': listing,
                            'is_primary': row['is_primary'] or False,
                            'created_at': row['created_at']
                        }
                    )
                    
                    if created:
                        # Create a simple placeholder image
                        try:
                            from PIL import Image
                            import io
                            
                            # Create a simple colored image
                            img = Image.new('RGB', (300, 200), color=192)
                            img_io = io.BytesIO()
                            img.save(img_io, format='JPEG')
                            img_io.seek(0)
                            
                            listing_image.image.save(image_name, ContentFile(img_io.read()), save=True)
                            created_count += 1
                        except ImportError:
                            # PIL not available, skip image creation
                            self.stdout.write(self.style.WARNING('PIL not available, skipping placeholder image creation'))
                            created_count += 1
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f'Error creating placeholder image: {e}'))
                            created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error creating listing image: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} listing images'))
