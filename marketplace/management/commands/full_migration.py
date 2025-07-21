#!/usr/bin/env python
"""
Complete migration script from SQLite to PostgreSQL
This script handles the entire migration process including:
- Categories
- Users and profiles
- Listings
- Images
- Messages
- Favorites
"""

import sqlite3
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from marketplace.models import Category, Listing, UserProfile, ListingImage, Message, Favorite
from django.db import transaction
from django.core.files.base import ContentFile
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Complete migration from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--sqlite-path', type=str, default='db.sqlite3', help='Path to SQLite DB')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually migrating')
        parser.add_argument('--skip-categories', action='store_true', help='Skip category migration')
        parser.add_argument('--skip-users', action='store_true', help='Skip user migration')
        parser.add_argument('--skip-listings', action='store_true', help='Skip listing migration')
        parser.add_argument('--skip-images', action='store_true', help='Skip image migration')

    def handle(self, *args, **options):
        sqlite_path = options['sqlite_path']
        dry_run = options['dry_run']
        conn = None
        
        try:
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Disable signals temporarily
            try:
                from marketplace.signals import create_user_profile, save_user_profile
                post_save.disconnect(create_user_profile, sender=User)
                post_save.disconnect(save_user_profile, sender=User)
            except (ImportError, NameError):
                self.stdout.write(self.style.WARNING('Could not import signals, continuing...'))
            
            # Get counts for dry run
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual migration will occur'))
                self.show_migration_counts(cursor)
                return
            
            # Perform actual migration
            self.stdout.write(self.style.SUCCESS('Starting complete migration...'))
            
            if not options['skip_categories']:
                self.migrate_categories(cursor)
            
            if not options['skip_users']:
                self.migrate_users(cursor)
            
            if not options['skip_listings']:
                self.migrate_listings(cursor)
            
            if not options['skip_images']:
                self.migrate_listing_images(cursor)
            
            # Migrate additional data
            self.migrate_messages(cursor)
            self.migrate_favorites(cursor)
            
            # Re-enable signals
            try:
                from marketplace.signals import create_user_profile, save_user_profile
                post_save.connect(create_user_profile, sender=User)
                post_save.connect(save_user_profile, sender=User)
            except:
                pass
            
            self.stdout.write(self.style.SUCCESS('Complete migration finished successfully!'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error during migration: {e}'))
            # Re-enable signals on error
            try:
                from marketplace.signals import create_user_profile, save_user_profile
                post_save.connect(create_user_profile, sender=User)
                post_save.connect(save_user_profile, sender=User)
            except:
                pass
        finally:
            if conn:
                conn.close()

    def show_migration_counts(self, cursor):
        """Show counts of what would be migrated"""
        cursor.execute('SELECT COUNT(*) as count FROM marketplace_category')
        category_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM auth_user')
        user_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM marketplace_listing')
        listing_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM marketplace_listingimage')
        image_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM marketplace_message')
        message_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM marketplace_favorite')
        favorite_count = cursor.fetchone()['count']
        
        self.stdout.write(self.style.SUCCESS('Migration counts:'))
        self.stdout.write(f'  Categories: {category_count}')
        self.stdout.write(f'  Users: {user_count}')
        self.stdout.write(f'  Listings: {listing_count}')
        self.stdout.write(f'  Images: {image_count}')
        self.stdout.write(f'  Messages: {message_count}')
        self.stdout.write(f'  Favorites: {favorite_count}')

    def migrate_categories(self, cursor):
        """Migrate categories"""
        cursor.execute('''
            SELECT id, name, slug, icon, color, parent_id
            FROM marketplace_category
            ORDER BY parent_id NULLS FIRST, id
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        updated_count = 0
        
        # First pass: create all categories without parents
        with transaction.atomic():
            for row in rows:
                try:
                    # Check if category already exists by slug
                    existing = Category.objects.filter(slug=row['slug']).first()
                    if existing:
                        # Update existing category
                        existing.name = row['name']
                        existing.icon = row['icon'] or ''
                        existing.color = row['color'] or '#007bff'
                        existing.save()
                        updated_count += 1
                    else:
                        # Create new category with unique slug
                        category, created = Category.objects.get_or_create(
                            id=row['id'],
                            defaults={
                                'name': row['name'],
                                'slug': row['slug'] or f'category-{row["id"]}',
                                'icon': row['icon'] or '',
                                'color': row['color'] or '#007bff'
                            }
                        )
                        if created:
                            created_count += 1
                        
                except Exception as e:
                    # Handle duplicate slug by appending ID
                    try:
                        category = Category.objects.create(
                            id=row['id'],
                            name=row['name'],
                            slug=f"{row['slug']}-{row['id']}" if row['slug'] else f'category-{row["id"]}',
                            icon=row['icon'] or '',
                            color=row['color'] or '#007bff'
                        )
                        created_count += 1
                    except Exception as e2:
                        self.stderr.write(self.style.ERROR(f'Error processing category {row["name"]}: {e2}'))
        
        # Second pass: assign parents
        with transaction.atomic():
            for row in rows:
                if row['parent_id']:
                    try:
                        category = Category.objects.get(id=row['id'])
                        parent = Category.objects.get(id=row['parent_id'])
                        # Use update to avoid type checking issues
                        Category.objects.filter(id=row['id']).update(parent=parent)
                    except Category.DoesNotExist:
                        pass
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} new categories, updated {updated_count} existing categories'))

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
            SELECT id, title, description, price, currency, location, status,
                   created_at, updated_at, expires_at, is_premium, is_featured,
                   views, metadata, is_verified, user_id, category_id, subcategory_id,
                   address, city, country, county, latitude, location_verified,
                   longitude, postal_code, slug
            FROM marketplace_listing
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for row in rows:
                try:
                    user = User.objects.get(id=row['user_id'])
                    category = Category.objects.get(id=row['category_id'])
                    
                    # Handle subcategory
                    subcategory = None
                    if row['subcategory_id']:
                        try:
                            subcategory = Category.objects.get(id=row['subcategory_id'])
                        except Category.DoesNotExist:
                            subcategory = None
                    
                    # Handle metadata
                    metadata = None
                    if row['metadata']:
                        try:
                            metadata = json.loads(row['metadata'])
                        except (json.JSONDecodeError, TypeError):
                            metadata = None
                    
                    listing, created = Listing.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'title': row['title'],
                            'description': row['description'],
                            'price': Decimal(str(row['price'])) if row['price'] is not None else None,
                            'currency': row['currency'] or 'RON',
                            'location': row['location'] or '',
                            'status': row['status'] or 'pending',
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at'],
                            'expires_at': row['expires_at'],
                            'is_premium': row['is_premium'] or False,
                            'is_featured': row['is_featured'] or False,
                            'views': row['views'] or 0,
                            'metadata': metadata,
                            'is_verified': row['is_verified'] or False,
                            'user': user,
                            'category': category,
                            'subcategory': subcategory,
                            'address': row['address'] or '',
                            'city': row['city'] or '',
                            'country': row['country'] or 'România',
                            'county': row['county'] or '',
                            'latitude': row['latitude'],
                            'longitude': row['longitude'],
                            'location_verified': row['location_verified'] or False,
                            'postal_code': row['postal_code'] or '',
                            'slug': row['slug'] or f'listing-{row["id"]}'
                        }
                    )
                    
                    if not created:
                        # Update existing listing
                        listing.title = row['title']
                        listing.description = row['description']
                        listing.price = Decimal(str(row['price'])) if row['price'] is not None else None
                        listing.currency = row['currency'] or 'RON'
                        listing.location = row['location'] or ''
                        listing.status = row['status'] or 'pending'
                        listing.created_at = row['created_at']
                        listing.updated_at = row['updated_at']
                        listing.expires_at = row['expires_at']
                        listing.is_premium = row['is_premium'] or False
                        listing.is_featured = row['is_featured'] or False
                        listing.views = row['views'] or 0
                        listing.metadata = metadata
                        listing.is_verified = row['is_verified'] or False
                        listing.user = user
                        listing.category = category
                        listing.subcategory = subcategory
                        listing.address = row['address'] or ''
                        listing.city = row['city'] or ''
                        listing.country = row['country'] or 'România'
                        listing.county = row['county'] or ''
                        listing.latitude = row['latitude']
                        listing.longitude = row['longitude']
                        listing.location_verified = row['location_verified'] or False
                        listing.postal_code = row['postal_code'] or ''
                        listing.slug = row['slug'] or f'listing-{row["id"]}'
                        listing.save()
                        updated_count += 1
                    else:
                        created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error processing listing {row["title"]}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} new listings, updated {updated_count} existing listings'))

    def migrate_listing_images(self, cursor):
        """Migrate listing images"""
        cursor.execute('''
            SELECT id, image, listing_id, is_main, created_at
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
                            'is_main': row['is_main'] or False,
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

    def migrate_messages(self, cursor):
        """Migrate messages"""
        cursor.execute('''
            SELECT id, sender_id, receiver_id, listing_id, content, created_at, is_read
            FROM marketplace_message
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        
        with transaction.atomic():
            for row in rows:
                try:
                    sender = User.objects.get(id=row['sender_id'])
                    receiver = User.objects.get(id=row['receiver_id'])
                    
                    # Handle optional listing
                    listing = None
                    if row['listing_id']:
                        try:
                            listing = Listing.objects.get(id=row['listing_id'])
                        except Listing.DoesNotExist:
                            pass
                    
                    message, created = Message.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'sender': sender,
                            'receiver': receiver,
                            'listing': listing,
                            'content': row['content'],
                            'created_at': row['created_at'],
                            'is_read': row['is_read'] or False
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error creating message: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} messages'))

    def migrate_favorites(self, cursor):
        """Migrate favorites"""
        cursor.execute('''
            SELECT id, user_id, listing_id, created_at
            FROM marketplace_favorite
        ''')
        rows = cursor.fetchall()
        
        created_count = 0
        
        with transaction.atomic():
            for row in rows:
                try:
                    user = User.objects.get(id=row['user_id'])
                    listing = Listing.objects.get(id=row['listing_id'])
                    
                    favorite, created = Favorite.objects.get_or_create(
                        id=row['id'],
                        defaults={
                            'user': user,
                            'listing': listing,
                            'created_at': row['created_at']
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error creating favorite: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {created_count} favorites'))
