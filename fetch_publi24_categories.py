#!/usr/bin/env python3
"""
Fetch categories from publi24.ro and update the database
"""

import os
import sys
import django
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piata_ro.settings')
django.setup()

from marketplace.models import Category

class Publi24CategoryScraper:
    def __init__(self):
        self.base_url = "https://www.publi24.ro"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.categories_data = {}
        
    def fetch_main_page(self):
        """Fetch the main page to get category structure"""
        try:
            print("🔍 Fetching publi24.ro main page...")
            response = self.session.get(self.base_url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Error fetching main page: {e}")
            return None
    
    def extract_categories_from_soup(self, soup):
        """Extract categories from the BeautifulSoup object"""
        categories = {}
        
        # Look for category navigation or menu
        category_selectors = [
            'nav .category-menu',
            '.categories-list',
            '.main-categories',
            'nav ul li a',
            '.nav-categories',
            '.category-nav'
        ]
        
        for selector in category_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"✅ Found categories with selector: {selector}")
                for element in elements:
                    self.parse_category_element(element, categories)
                break
        
        # If no specific category structure found, look for general links
        if not categories:
            print("🔍 Looking for category links in navigation...")
            nav_links = soup.find_all('a', href=True)
            for link in nav_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Filter category-like URLs
                if (href.startswith('/') or href.startswith(self.base_url)) and text and len(text) > 2:
                    # Skip common non-category links
                    skip_patterns = ['login', 'register', 'contact', 'about', 'help', 'privacy', 'terms']
                    if not any(pattern in href.lower() or pattern in text.lower() for pattern in skip_patterns):
                        if len(text) < 50:  # Reasonable category name length
                            categories[text] = {
                                'name': text,
                                'url': href,
                                'subcategories': {}
                            }
        
        return categories
    
    def parse_category_element(self, element, categories):
        """Parse individual category element"""
        try:
            text = element.get_text(strip=True)
            href = element.get('href', '')
            
            if text and href:
                categories[text] = {
                    'name': text,
                    'url': href,
                    'subcategories': {}
                }
        except Exception as e:
            print(f"⚠️ Error parsing category element: {e}")
    
    def get_predefined_categories(self):
        """Get predefined Romanian marketplace categories based on common patterns"""
        return {
            # Imobiliare
            "Imobiliare": {
                "name": "Imobiliare",
                "icon": "fas fa-home",
                "color": "#4CAF50",
                "subcategories": {
                    "Apartamente de vânzare": {"name": "Apartamente de vânzare", "icon": "far fa-building"},
                    "Apartamente de închiriat": {"name": "Apartamente de închiriat", "icon": "far fa-building"},
                    "Case de vânzare": {"name": "Case de vânzare", "icon": "fas fa-home"},
                    "Case de închiriat": {"name": "Case de închiriat", "icon": "fas fa-home"},
                    "Terenuri": {"name": "Terenuri", "icon": "fas fa-map-marked-alt"},
                    "Spații comerciale/Birouri": {"name": "Spații comerciale/Birouri", "icon": "fas fa-store"},
                    "Cazare/Turism": {"name": "Cazare/Turism", "icon": "fas fa-hotel"},
                    "Garaje": {"name": "Garaje", "icon": "fas fa-warehouse"},
                    "Depozite": {"name": "Depozite", "icon": "fas fa-warehouse"},
                }
            },
            
            # Auto, Moto și Ambarcațiuni
            "Auto, Moto și Ambarcațiuni": {
                "name": "Auto, Moto și Ambarcațiuni",
                "icon": "fas fa-car",
                "color": "#2196F3",
                "subcategories": {
                    "Autoturisme": {"name": "Autoturisme", "icon": "fas fa-car-side"},
                    "Motociclete/Scutere/ATV": {"name": "Motociclete/Scutere/ATV", "icon": "fas fa-motorcycle"},
                    "Rulote/Autorulote": {"name": "Rulote/Autorulote", "icon": "fas fa-caravan"},
                    "Camioane/Utilaje": {"name": "Camioane/Utilaje", "icon": "fas fa-truck"},
                    "Ambarcațiuni": {"name": "Ambarcațiuni", "icon": "fas fa-ship"},
                    "Piese Auto": {"name": "Piese Auto", "icon": "fas fa-cogs"},
                    "Servicii Auto": {"name": "Servicii Auto", "icon": "fas fa-tools"},
                    "Anvelope și Jante": {"name": "Anvelope și Jante", "icon": "fas fa-circle"},
                    "Accesorii Auto": {"name": "Accesorii Auto", "icon": "fas fa-car-battery"},
                }
            },
            
            # Electronice și Electrocasnice
            "Electronice și Electrocasnice": {
                "name": "Electronice și Electrocasnice",
                "icon": "fas fa-laptop",
                "color": "#FF9800",
                "subcategories": {
                    "Telefoane": {"name": "Telefoane", "icon": "fas fa-mobile-alt"},
                    "Calculatoare/Laptopuri": {"name": "Calculatoare/Laptopuri", "icon": "fas fa-laptop"},
                    "TV/Audio/Video": {"name": "TV/Audio/Video", "icon": "fas fa-tv"},
                    "Electrocasnice Mari": {"name": "Electrocasnice Mari", "icon": "fas fa-blender"},
                    "Electrocasnice Mici": {"name": "Electrocasnice Mici", "icon": "fas fa-coffee"},
                    "Jocuri/Console": {"name": "Jocuri/Console", "icon": "fas fa-gamepad"},
                    "Aparate Foto/Video": {"name": "Aparate Foto/Video", "icon": "fas fa-camera-retro"},
                    "Tablete": {"name": "Tablete", "icon": "fas fa-tablet-alt"},
                    "Accesorii Electronice": {"name": "Accesorii Electronice", "icon": "fas fa-headphones"},
                    "Smart Home": {"name": "Smart Home", "icon": "fas fa-home"},
                }
            },
            
            # Modă și Frumusețe
            "Modă și Frumusețe": {
                "name": "Modă și Frumusețe",
                "icon": "fas fa-tshirt",
                "color": "#E91E63",
                "subcategories": {
                    "Haine Damă": {"name": "Haine Damă", "icon": "fas fa-female"},
                    "Haine Bărbați": {"name": "Haine Bărbați", "icon": "fas fa-male"},
                    "Haine Copii": {"name": "Haine Copii", "icon": "fas fa-child"},
                    "Încălțăminte": {"name": "Încălțăminte", "icon": "fas fa-shoe-prints"},
                    "Accesorii (Genți, Ceasuri, Bijuterii)": {"name": "Accesorii (Genți, Ceasuri, Bijuterii)", "icon": "fas fa-gem"},
                    "Cosmetice/Parfumuri": {"name": "Cosmetice/Parfumuri", "icon": "fas fa-magic"},
                    "Ochelari": {"name": "Ochelari", "icon": "fas fa-glasses"},
                    "Haine Vintage": {"name": "Haine Vintage", "icon": "fas fa-tshirt"},
                }
            },
            
            # Casă și Grădină
            "Casă și Grădină": {
                "name": "Casă și Grădină",
                "icon": "fas fa-leaf",
                "color": "#8BC34A",
                "subcategories": {
                    "Mobilier": {"name": "Mobilier", "icon": "fas fa-couch"},
                    "Decorațiuni/Artă": {"name": "Decorațiuni/Artă", "icon": "fas fa-paint-brush"},
                    "Gradină/Terasă": {"name": "Gradină/Terasă", "icon": "fas fa-seedling"},
                    "Scule și Unelte": {"name": "Scule și Unelte", "icon": "fas fa-hammer"},
                    "Materiale de Construcție": {"name": "Materiale de Construcție", "icon": "fas fa-hard-hat"},
                    "Instalații": {"name": "Instalații", "icon": "fas fa-wrench"},
                    "Textile Casă": {"name": "Textile Casă", "icon": "fas fa-blanket"},
                    "Vase și Tacâmuri": {"name": "Vase și Tacâmuri", "icon": "fas fa-utensils"},
                }
            },
            
            # Sport, Timp Liber, Artă
            "Sport, Timp Liber, Artă": {
                "name": "Sport, Timp Liber, Artă",
                "icon": "fas fa-futbol",
                "color": "#FFC107",
                "subcategories": {
                    "Echipamente Sportive": {"name": "Echipamente Sportive", "icon": "fas fa-dumbbell"},
                    "Biciclete": {"name": "Biciclete", "icon": "fas fa-bicycle"},
                    "Fitness/Sală": {"name": "Fitness/Sală", "icon": "fas fa-dumbbell"},
                    "Sporturi de Apă": {"name": "Sporturi de Apă", "icon": "fas fa-swimmer"},
                    "Drumeții/Camping": {"name": "Drumeții/Camping", "icon": "fas fa-campground"},
                    "Vânătoare/Pescuit": {"name": "Vânătoare/Pescuit", "icon": "fas fa-fish"},
                    "Muzică/Instrumente": {"name": "Muzică/Instrumente", "icon": "fas fa-music"},
                    "Cărți/Reviste": {"name": "Cărți/Reviste", "icon": "fas fa-book"},
                    "Colecții": {"name": "Colecții", "icon": "fas fa-coins"},
                    "Jocuri/Jucării": {"name": "Jocuri/Jucării", "icon": "fas fa-puzzle-piece"},
                }
            },
            
            # Locuri de Muncă
            "Locuri de Muncă": {
                "name": "Locuri de Muncă",
                "icon": "fas fa-briefcase",
                "color": "#9C27B0",
                "subcategories": {
                    "IT/Software": {"name": "IT/Software", "icon": "fas fa-code"},
                    "Vânzări/Marketing": {"name": "Vânzări/Marketing", "icon": "fas fa-chart-line"},
                    "Educație": {"name": "Educație", "icon": "fas fa-graduation-cap"},
                    "Sănătate": {"name": "Sănătate", "icon": "fas fa-user-md"},
                    "Construcții": {"name": "Construcții", "icon": "fas fa-hard-hat"},
                    "Transport/Logistică": {"name": "Transport/Logistică", "icon": "fas fa-truck"},
                    "HoReCa": {"name": "HoReCa", "icon": "fas fa-utensils"},
                    "Administrație": {"name": "Administrație", "icon": "fas fa-clipboard-list"},
                    "Producție": {"name": "Producție", "icon": "fas fa-industry"},
                    "Freelancing": {"name": "Freelancing", "icon": "fas fa-laptop-house"},
                }
            },
            
            # Servicii, Afaceri, Echipamente Firme
            "Servicii, Afaceri, Echipamente Firme": {
                "name": "Servicii, Afaceri, Echipamente Firme",
                "icon": "fas fa-concierge-bell",
                "color": "#3F51B5",
                "subcategories": {
                    "Servicii IT": {"name": "Servicii IT", "icon": "fas fa-laptop-code"},
                    "Consultanță": {"name": "Consultanță", "icon": "fas fa-handshake"},
                    "Servicii Financiare": {"name": "Servicii Financiare", "icon": "fas fa-chart-pie"},
                    "Servicii Juridice": {"name": "Servicii Juridice", "icon": "fas fa-gavel"},
                    "Servicii Medicale": {"name": "Servicii Medicale", "icon": "fas fa-stethoscope"},
                    "Traduceri": {"name": "Traduceri", "icon": "fas fa-language"},
                    "Echipamente Birou": {"name": "Echipamente Birou", "icon": "fas fa-desktop"},
                    "Servicii Curățenie": {"name": "Servicii Curățenie", "icon": "fas fa-broom"},
                    "Servicii Transport": {"name": "Servicii Transport", "icon": "fas fa-shipping-fast"},
                }
            },
            
            # Mama și Copilul
            "Mama și Copilul": {
                "name": "Mama și Copilul",
                "icon": "fas fa-child",
                "color": "#00BCD4",
                "subcategories": {
                    "Îmbrăcăminte Copii": {"name": "Îmbrăcăminte Copii", "icon": "fas fa-baby"},
                    "Jucării": {"name": "Jucării", "icon": "fas fa-teddy-bear"},
                    "Cărucioare/Scaune Auto": {"name": "Cărucioare/Scaune Auto", "icon": "fas fa-baby-carriage"},
                    "Mobilier Copii": {"name": "Mobilier Copii", "icon": "fas fa-bed"},
                    "Hrană Bebeluși": {"name": "Hrană Bebeluși", "icon": "fas fa-baby-carriage"},
                    "Cărți Copii": {"name": "Cărți Copii", "icon": "fas fa-book-open"},
                    "Articole Sarcină": {"name": "Articole Sarcină", "icon": "fas fa-female"},
                    "Echipamente Siguranță": {"name": "Echipamente Siguranță", "icon": "fas fa-shield-alt"},
                }
            },
            
            # Animale de Companie
            "Animale de Companie": {
                "name": "Animale de Companie",
                "icon": "fas fa-paw",
                "color": "#607D8B",
                "subcategories": {
                    "Câini": {"name": "Câini", "icon": "fas fa-dog"},
                    "Pisici": {"name": "Pisici", "icon": "fas fa-cat"},
                    "Păsări": {"name": "Păsări", "icon": "fas fa-dove"},
                    "Pești": {"name": "Pești", "icon": "fas fa-fish"},
                    "Animale Mici": {"name": "Animale Mici", "icon": "fas fa-rabbit"},
                    "Accesorii Animale": {"name": "Accesorii Animale", "icon": "fas fa-bone"},
                    "Hrană Animale": {"name": "Hrană Animale", "icon": "fas fa-cookie-bite"},
                    "Servicii Veterinare": {"name": "Servicii Veterinare", "icon": "fas fa-user-md"},
                }
            },
            
            # Agro și Industrie
            "Agro și Industrie": {
                "name": "Agro și Industrie",
                "icon": "fas fa-tractor",
                "color": "#795548",
                "subcategories": {
                    "Utilaje Agricole": {"name": "Utilaje Agricole", "icon": "fas fa-tractor"},
                    "Animale de Fermă": {"name": "Animale de Fermă", "icon": "fas fa-horse"},
                    "Semințe/Plante": {"name": "Semințe/Plante", "icon": "fas fa-seedling"},
                    "Echipamente Industriale": {"name": "Echipamente Industriale", "icon": "fas fa-industry"},
                    "Produse Chimice": {"name": "Produse Chimice", "icon": "fas fa-flask"},
                    "Utilaje Construcții": {"name": "Utilaje Construcții", "icon": "fas fa-hammer"},
                }
            }
        }
    
    def update_database(self, categories_data):
        """Update the database with fetched categories"""
        print("📊 Updating database with categories...")
        created_count = 0
        updated_count = 0
        
        # Filter out navigation items that aren't actual categories
        skip_categories = [
            'publi24.ro', 'Adaugă anunț', 'Acasă', 'Favorite', 'Vinde', 
            'Mesaje', 'Cont', 'Login', 'Register', 'Search', 'Help',
            'Contact', 'About', 'Privacy', 'Terms', 'Blog', 'News'
        ]
        
        for main_cat_name, main_cat_data in categories_data.items():
            # Skip navigation items
            if main_cat_name in skip_categories:
                continue
                
            try:
                # Create or update main category
                main_category, created = Category.objects.get_or_create(
                    name=main_cat_name,
                    parent=None,
                    defaults={
                        'slug': self.create_slug(main_cat_name),
                        'icon': main_cat_data.get('icon', 'fas fa-folder'),
                        'color': main_cat_data.get('color', '#607D8B')
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"✅ Created main category: {main_cat_name}")
                else:
                    updated_count += 1
                    # Update icon and color if provided
                    if 'icon' in main_cat_data:
                        main_category.icon = main_cat_data['icon']
                    if 'color' in main_cat_data:
                        main_category.color = main_cat_data['color']
                    main_category.save()
                    print(f"🔄 Updated main category: {main_cat_name}")
                
                # Create subcategories
                subcategories = main_cat_data.get('subcategories', {})
                for sub_cat_name, sub_cat_data in subcategories.items():
                    try:
                        subcategory, sub_created = Category.objects.get_or_create(
                            name=sub_cat_name,
                            parent=main_category,
                            defaults={
                                'slug': self.create_slug(sub_cat_name),
                                'icon': sub_cat_data.get('icon', 'fas fa-tag'),
                                'color': main_cat_data.get('color', '#607D8B')
                            }
                        )
                        
                        if sub_created:
                            created_count += 1
                            print(f"  ✅ Created subcategory: {sub_cat_name}")
                        else:
                            # Update icon if provided
                            if 'icon' in sub_cat_data:
                                subcategory.icon = sub_cat_data['icon']
                                subcategory.save()
                            print(f"  🔄 Updated subcategory: {sub_cat_name}")
                    except Exception as sub_error:
                        print(f"  ❌ Error creating subcategory {sub_cat_name}: {sub_error}")
                        
            except Exception as main_error:
                print(f"❌ Error creating main category {main_cat_name}: {main_error}")
        
        print(f"📈 Database update complete: {created_count} created, {updated_count} updated")
        return created_count, updated_count
    
    def create_slug(self, name):
        """Create URL-friendly slug from category name"""
        # Romanian character mapping
        romanian_chars = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
        }
        
        slug = name.lower()
        for ro_char, en_char in romanian_chars.items():
            slug = slug.replace(ro_char, en_char)
        
        # Remove special characters and replace spaces with hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure slug is unique
        original_slug = slug
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug
    
    def run(self):
        """Main execution method"""
        print("🚀 Starting Publi24 category scraping...")
        
        # Try to fetch from website first
        soup = self.fetch_main_page()
        if soup:
            scraped_categories = self.extract_categories_from_soup(soup)
            if scraped_categories:
                print(f"✅ Found {len(scraped_categories)} categories from website")
                self.categories_data.update(scraped_categories)
        
        # Use predefined categories (comprehensive Romanian marketplace categories)
        predefined_categories = self.get_predefined_categories()
        print(f"📋 Using {len(predefined_categories)} predefined categories")
        self.categories_data.update(predefined_categories)
        
        # Update database
        if self.categories_data:
            created, updated = self.update_database(self.categories_data)
            
            # Show summary
            total_categories = Category.objects.count()
            main_categories = Category.objects.filter(parent=None).count()
            subcategories = Category.objects.filter(parent__isnull=False).count()
            
            print("\n📊 Category Summary:")
            print(f"   Total categories: {total_categories}")
            print(f"   Main categories: {main_categories}")
            print(f"   Subcategories: {subcategories}")
            print(f"   Created: {created}")
            print(f"   Updated: {updated}")
            
            return True
        else:
            print("❌ No categories found to update")
            return False

if __name__ == "__main__":
    scraper = Publi24CategoryScraper()
    success = scraper.run()
    
    if success:
        print("\n✅ Category update completed successfully!")
    else:
        print("\n❌ Category update failed!")
