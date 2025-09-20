from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup, Tag
from marketplace.models import Category
import re
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch and populate categories from Publi24 website'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting Publi24 category scraping...')

        scraper = Publi24CategoryScraper(stdout=self.stdout)
        success = scraper.run()

        if success:
            self.stdout.write('✅ Categories fetched and populated successfully!')
        else:
            self.stdout.write('❌ Error occurred during category fetching')

class Publi24CategoryScraper:
    def __init__(self, stdout=None):
        self.base_url = "https://www.publi24.ro"
        self.categories_found = 0
        self.stdout = stdout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def output(self, message):
        if self.stdout is not None:
            self.stdout.write(message)
        else:
            print(message)

    def fetch_page(self, url):
        """Fetch a page with error handling"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.output(f"❌ Error fetching {url}: {str(e)}")
            return None

    def scrape_categories(self):
        """Scrape categories from publi24.ro"""
        self.output('🔍 Fetching publi24.ro main page...')

        html = self.fetch_page(self.base_url)
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        categories = {}

        # Find category navigation
        self.output('🔍 Looking for category links in navigation...')

        # Look for navigation containers
        nav_selectors = [
            'nav', '.navigation', '.nav-primary', '.main-navigation',
            '[class*="nav"]', '[id*="nav"]',
            'header nav', '.header nav'
        ]

        category_links = set()

        for selector in nav_selectors:
            nav_elements = soup.select(selector)
            for nav in nav_elements:
                links = nav.find_all('a', href=True)
                for link in links:
                    if isinstance(link, Tag):
                        href = str(link.attrs.get('href', ''))
                        text = link.get_text(strip=True) or ''

                        # Filter for category-like links
                        if href and any(keyword in text.lower() for keyword in
                            ['imobiliare', 'auto', 'moto', 'job', 'servicii', 'electronice',
                             'modă', 'casă', 'animale', 'timp liber', 'sport', 'turism',
                             'cazare', 'munca', 'afaceri', 'industrie', 'agricultura']) or \
                           any(keyword in href.lower() for keyword in
                            ['categorie', 'category', 'imobiliare', 'auto', 'job']):
                            category_links.add((href, text))

        self.output(f'✅ Found {len(category_links)} categories from website')

        # Use predefined categories if scraping didn't work
        if len(category_links) < 10:
            self.output('📋 Using predefined categories')

            predefined_categories = [
                'Imobiliare',  # Real Estate
                'Locuri de Muncă',  # Jobs
                'Auto, Moto și Ambarcațiuni',  # Auto & Transport
                'Electronice și Electrocasnice',  # Electronics
                'Modă și Frumusețe',  # Fashion & Beauty
                'Casă și Grădină',  # Home & Garden
                'Mama și Copilul',  # Baby & Kids
                'Animale de Companie',  # Pets
                'Servicii, Afaceri, Echipamente Firme',  # Services & Business
                'Matrimoniale',  # Matrimonial/Dating
                'Sport, Timp Liber, Artă',  # Sports & Leisure
                'Agro și Industrie',  # Agri & Industry
                'Cazare turism'  # Tourism & Hotels
            ]

            # Add comprehensive subcategories
            predefined_subcategories = {
                'Imobiliare': ['Apartamente de vânzare', 'Case de vânzare', 'Apartamente de închiriere', 'Birouri de închiriat'],
                'Auto, Moto și Ambarcațiuni': ['Mașini', 'Motociclete', 'Camioane', 'Piese auto'],
                'Locuri de Muncă': ['IT/Călculatoare', 'Construcții', 'Administrație', 'Finanțe'],
                'Electronice și Electrocasnice': ['Telefoane', 'Laptop/Calc PC', 'Tvs', 'Electrocasnice'],
                'Modă și Frumusețe': ['Haine Dama', 'Haine Barbati', 'Încălțaminte', 'Accesorii'],
                'Casă și Grădină': ['Mobilă', 'Decorațiuni', 'Grădinărie', 'Electrocasnice'],
                'Mama și Copilul': ['Mobilă copii', 'Jucării', 'Hăinuțe copii', 'Cărucioare/Scaune'],
                'Animale de Companie': ['Câini', 'Pisici', 'Păsări', 'Pești'],
                'Sport, Timp Liber, Artă': ['Sport', 'Cărți', 'Colecționării', 'Hobby']
            }

            categories = {cat: [] for cat in predefined_categories}

        else:
            # Process scraped categories
            for href, text in category_links:
                if len(text.split()) <= 6:  # Only main categories
                    categories[text] = []

        return categories

    def populate_database(self, categories):
        """Populate database with scraped categories"""
        self.output('📊 Updating database with categories...')

        created_count = 0
        updated_count = 0
        subcategory_count = 0

        try:
            Category.objects.all().delete()  # Clear existing categories
            self.output('🗑️ Cleared existing categories')
        except Exception as e:
            self.output(f'⚠️ Warning: Could not clear categories: {e}')

        # Icons and colors for categories
        category_icons = {
            'imobiliare': 'fa-home',
            'auto': 'fa-car',
            'moto': 'fa-motorcycle',
            'job': 'fa-briefcase',
            'servicii': 'fa-wrench',
            'electronice': 'fa-mobile-alt',
            'modă': 'fa-tshirt',
            'casă': 'fa-tools',
            'animale': 'fa-paw',
            'timp': 'fa-futbol',
            'sport': 'fa-running',
            'turism': 'fa-map-marker-alt',
            'mamă': 'fa-baby',
            'copil': 'fa-child'
        }

        category_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
            '#F7DC6F', '#BB8FCE', '#85C1E9', '#82E0AA', '#F8C471',
            '#58D68D', '#AF7AC5'
        ]

        # First, create main categories
        main_categories = {}
        for i, category_name in enumerate(categories.keys()):
            try:
                clean_name = category_name.strip()
                icon = 'fa-tag'
                for key, value in category_icons.items():
                    if key in clean_name.lower():
                        icon = value
                        break
                color = category_colors[i % len(category_colors)]

                category, created = Category.objects.get_or_create(
                    name=clean_name,
                    defaults={
                        'slug': self.slugify(clean_name),
                        'icon': icon,
                        'color': color,
                        'parent': None  # Ensure main categories have no parent
                    }
                )
                main_categories[clean_name] = category

                if created:
                    created_count += 1
                    self.output(f'✅ Created main category: {clean_name}')
                else:
                    updated_count += 1
                    self.output(f'↺ Updated main category: {clean_name}')

            except Exception as e:
                self.output(f'❌ Error creating main category {category_name}: {str(e)}')

        # Now create subcategories using predefined structure
        predefined_subcategories = {
            'Imobiliare': ['Apartamente de vânzare', 'Case de vânzare', 'Apartamente de închiriere', 'Birouri de închiriat'],
            'Auto, Moto și Ambarcațiuni': ['Mașini', 'Motociclete', 'Camioane', 'Piese auto'],
            'Locuri de Muncă': ['IT/Călculatoare', 'Construcții', 'Administrație', 'Finanțe'],
            'Electronice și Electrocasnice': ['Telefoane', 'Laptop/Calc PC', 'Tvs', 'Electrocasnice'],
            'Modă și Frumusețe': ['Haine Dama', 'Haine Barbati', 'Încălțaminte', 'Accesorii'],
            'Casă și Grădină': ['Mobilă', 'Decorațiuni', 'Grădinărie', 'Electrocasnice'],
            'Mama și Copilul': ['Mobilă copii', 'Jucării', 'Hăinuțe copii', 'Cărucioare/Scaune'],
            'Animale de Companie': ['Câini', 'Pisici', 'Păsări', 'Pești'],
            'Sport, Timp Liber, Artă': ['Sport', 'Cărți', 'Colecționării', 'Hobby'],
            'Servicii, Afaceri, Echipamente Firme': ['Servicii', 'Echipamente', 'Afaceri', 'Marketing']
        }

        for main_name, subcats in predefined_subcategories.items():
            if main_name in main_categories:
                parent = main_categories[main_name]
                for sub_name in subcats:
                    try:
                        sub_category, sub_created = Category.objects.get_or_create(
                            name=sub_name,
                            parent=parent,
                            defaults={
                                'slug': self.slugify(sub_name),
                                'icon': 'fa-tag',  # Subcats can have icons later
                                'color': category_colors[(list(main_categories.keys()).index(main_name) + 1) % len(category_colors)]
                            }
                        )
                        if sub_created:
                            subcategory_count += 1
                            self.output(f'✅ Created subcategory: {sub_name} under {main_name}')
                        else:
                            self.output(f'↺ Updated subcategory: {sub_name} under {main_name}')
                    except Exception as e:
                        self.output(f'❌ Error creating subcategory {sub_name}: {str(e)}')

        return created_count, updated_count, subcategory_count

    def slugify(self, text):
        """Create URL-friendly slug"""
        import unicodedata
        import re

        # Normalize unicode
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

        # Replace spaces with hyphens
        text = re.sub(r'[-\s]+', '-', text).lower()

        # Remove non-alphanumeric characters
        text = re.sub(r'[^a-z0-9-]', '', text)

        # Remove consecutive hyphens
        text = re.sub(r'-+', '-', text).strip('-')

        return text

    def run(self):
        """Main scraping workflow"""
        try:
            # Scrape categories
            categories = self.scrape_categories()

            # Populate database
            created, updated, subcats = self.populate_database(categories)

            total_categories = Category.objects.count()
            total_main = Category.objects.filter(parent__isnull=True).count()
            total_subs = Category.objects.filter(parent__isnull=False).count()

            self.output(f'📈 Database update complete: {created} main created, {updated} main updated, {subcats} subcategories')
            self.output(f'📊 Total: {total_categories} ({total_main} main + {total_subs} subcategories)')

            return True

        except Exception as e:
            self.output(f'❌ Error during scraping: {str(e)}')
            return False
