"""
Fix categories and add proper subcategories based on Publi24.ro structure
"""
from django.core.management.base import BaseCommand
from marketplace.models import Category

class Command(BaseCommand):
    help = 'Fix categories and add subcategories for monetization'

    def handle(self, *args, **options):
        self.stdout.write('Fixing categories and adding subcategories...')
        
        # Remove duplicates first
        self.remove_duplicates()
        
        # Create proper category structure
        self.create_category_structure()
        
        self.stdout.write(self.style.SUCCESS('Categories fixed successfully!'))

    def remove_duplicates(self):
        """Remove duplicate categories"""
        # Get all category names and find duplicates
        categories = Category.objects.all()
        seen_names = set()
        duplicates = []
        
        for category in categories:
            if category.name.lower() in seen_names:
                duplicates.append(category)
            else:
                seen_names.add(category.name.lower())
        
        # Delete duplicates
        for duplicate in duplicates:
            self.stdout.write(f'Removing duplicate: {duplicate.name}')
            duplicate.delete()

    def create_category_structure(self):
        """Create proper category structure based on Publi24.ro"""
        
        categories_structure = {
            'Matrimoniale': {
                'icon': 'fas fa-heart',
                'color': '#e91e63',
                'subcategories': [
                    'Femei caută bărbați',
                    'Bărbați caută femei', 
                    'Femei caută femei',
                    'Bărbați caută bărbați',
                    'Escorte',
                    'Masaj erotic',
                    'Matrimoniale străine',
                    'Matrimoniale mature',
                    'Matrimoniale tinere',
                    'Relații serioase',
                    'Aventuri',
                    'Prietenie'
                ]
            },
            'Locuri de muncă': {
                'icon': 'fas fa-briefcase',
                'color': '#2196f3',
                'subcategories': [
                    'IT & Software',
                    'Vânzări & Marketing',
                    'Administrație',
                    'Construcții',
                    'HoReCa',
                    'Transport & Logistică',
                    'Producție',
                    'Servicii',
                    'Freelancing',
                    'Lucru de acasă',
                    'Part-time',
                    'Internship'
                ]
            },
            'Imobiliare': {
                'icon': 'fas fa-home',
                'color': '#4caf50',
                'subcategories': [
                    'Apartamente de vânzare',
                    'Case de vânzare',
                    'Terenuri',
                    'Apartamente de închiriat',
                    'Case de închiriat',
                    'Spații comerciale/Birouri',
                    'Garaje',
                    'Depozite',
                    'Cazare turism'
                ]
            },
            'Auto, Moto și Ambarcațiuni': {
                'icon': 'fas fa-car',
                'color': '#ff9800',
                'subcategories': [
                    'Autoturisme',
                    'Motociclete/Scutere/ATV',
                    'Camioane/Utilaje',
                    'Ambarcațiuni',
                    'Rulote/Autorulote',
                    'Piese Auto',
                    'Anvelope și Jante',
                    'Accesorii Auto',
                    'Servicii Auto'
                ]
            },
            'Electronice și Electrocasnice': {
                'icon': 'fas fa-laptop',
                'color': '#9c27b0',
                'subcategories': [
                    'Telefoane',
                    'Calculatoare/Laptopuri',
                    'Tablete',
                    'TV/Audio/Video',
                    'Aparate Foto/Video',
                    'Jocuri/Console',
                    'Electrocasnice Mari',
                    'Electrocasnice Mici',
                    'Accesorii Electronice',
                    'Smart Home'
                ]
            },
            'Modă și Frumusețe': {
                'icon': 'fas fa-tshirt',
                'color': '#e91e63',
                'subcategories': [
                    'Haine Damă',
                    'Haine Bărbați',
                    'Haine Copii',
                    'Încălțăminte',
                    'Accesorii (Genți, Ceasuri, Bijuterii)',
                    'Cosmetice/Parfumuri',
                    'Ochelari',
                    'Haine Vintage'
                ]
            },
            'Casă și Grădină': {
                'icon': 'fas fa-home',
                'color': '#4caf50',
                'subcategories': [
                    'Mobilier',
                    'Mobilier Copii',
                    'Grădină/Terasă',
                    'Textile Casă',
                    'Vase și Tacâmuri',
                    'Decorațiuni/Artă',
                    'Scule și Unelte',
                    'Materiale de Construcție',
                    'Instalații'
                ]
            },
            'Sport, Timp Liber, Artă': {
                'icon': 'fas fa-futbol',
                'color': '#ff5722',
                'subcategories': [
                    'Echipamente Sportive',
                    'Biciclete',
                    'Fitness/Sală',
                    'Sporturi de Apă',
                    'Vânătoare/Pescuit',
                    'Drumeții/Camping',
                    'Muzică/Instrumente',
                    'Cărți/Reviste',
                    'Cărți Copii',
                    'Jocuri/Jucării',
                    'Colecții'
                ]
            },
            'Mama și Copilul': {
                'icon': 'fas fa-baby',
                'color': '#ffeb3b',
                'subcategories': [
                    'Îmbrăcăminte Copii',
                    'Jucării',
                    'Cărucioare/Scaune Auto',
                    'Hrană Bebeluși',
                    'Articole Sarcină'
                ]
            },
            'Animale': {
                'icon': 'fas fa-paw',
                'color': '#795548',
                'subcategories': [
                    'Câini',
                    'Pisici',
                    'Păsări',
                    'Pești',
                    'Animale Mici',
                    'Animale de Fermă',
                    'Animale de Companie',
                    'Accesorii Animale',
                    'Hrană Animale',
                    'Servicii Veterinare'
                ]
            },
            'Servicii, Afaceri, Echipamente Firme': {
                'icon': 'fas fa-tools',
                'color': '#607d8b',
                'subcategories': [
                    'Servicii IT',
                    'Servicii Curățenie',
                    'Servicii Transport',
                    'Servicii Medicale',
                    'Servicii Juridice',
                    'Servicii Financiare',
                    'Consultanță',
                    'Traduceri',
                    'Publicitate',
                    'Echipamente Birou',
                    'Echipamente Industriale',
                    'Echipamente Siguranță'
                ]
            },
            'Agro și Industrie': {
                'icon': 'fas fa-tractor',
                'color': '#8bc34a',
                'subcategories': [
                    'Utilaje Agricole',
                    'Utilaje Construcții',
                    'Semințe/Plante',
                    'Produse Chimice',
                    'HoReCa'
                ]
            },
            'Educație': {
                'icon': 'fas fa-graduation-cap',
                'color': '#3f51b5',
                'subcategories': [
                    'Cursuri',
                    'Meditații',
                    'Limbi străine',
                    'IT/Software',
                    'Artă/Muzică'
                ]
            },
            'Sănătate': {
                'icon': 'fas fa-heartbeat',
                'color': '#f44336',
                'subcategories': [
                    'Servicii medicale',
                    'Aparatură medicală',
                    'Suplimente',
                    'Echipamente fitness'
                ]
            }
        }
        
        for category_name, category_data in categories_structure.items():
            # Create or get parent category
            base_slug = category_name.lower().replace(' ', '-').replace(',', '').replace('&', 'si').replace('ă', 'a').replace('â', 'a').replace('î', 'i').replace('ș', 's').replace('ț', 't')
            
            # Check if category exists by name first
            try:
                parent_category = Category.objects.get(name=category_name)
                created = False
            except Category.DoesNotExist:
                # Generate unique slug
                slug = base_slug
                counter = 1
                while Category.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                parent_category = Category.objects.create(
                    name=category_name,
                    slug=slug,
                    icon=category_data.get('icon', 'fas fa-tag'),
                    color=category_data.get('color', '#6c757d')
                )
                created = True
            
            if created:
                self.stdout.write(f'Created parent category: {category_name}')
            
            # Create subcategories
            for subcategory_name in category_data['subcategories']:
                # Check if subcategory exists
                try:
                    subcategory = Category.objects.get(name=subcategory_name, parent=parent_category)
                    sub_created = False
                except Category.DoesNotExist:
                    # Generate unique slug for subcategory
                    base_sub_slug = subcategory_name.lower().replace(' ', '-').replace('/', '-').replace(',', '').replace('&', 'si').replace('ă', 'a').replace('â', 'a').replace('î', 'i').replace('ș', 's').replace('ț', 't')
                    sub_slug = base_sub_slug
                    counter = 1
                    while Category.objects.filter(slug=sub_slug).exists():
                        sub_slug = f"{base_sub_slug}-{counter}"
                        counter += 1
                    
                    subcategory = Category.objects.create(
                        name=subcategory_name,
                        parent=parent_category,
                        slug=sub_slug,
                        icon=category_data.get('icon', 'fas fa-tag'),
                        color=category_data.get('color', '#6c757d')
                    )
                    sub_created = True
                
                if sub_created:
                    self.stdout.write(f'  Created subcategory: {subcategory_name}')