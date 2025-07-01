"""
Create premium packages for monetization, especially for Matrimoniale
"""
from django.core.management.base import BaseCommand
from marketplace.models import CreditPackage, PremiumPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create premium packages for monetization'

    def handle(self, *args, **options):
        self.stdout.write('Creating premium packages...')
        
        # Credit packages
        credit_packages = [
            {
                'name': 'Pachet Starter',
                'credits': Decimal('5.0'),
                'price_eur': Decimal('5.00'),
                'price_ron': Decimal('25.00'),
                'description': 'Perfect pentru începători - 5 credite pentru promovare anunțuri'
            },
            {
                'name': 'Pachet Popular',
                'credits': Decimal('12.0'),
                'price_eur': Decimal('10.00'),
                'price_ron': Decimal('50.00'),
                'description': 'Cel mai popular - 12 credite cu 20% bonus'
            },
            {
                'name': 'Pachet Premium',
                'credits': Decimal('25.0'),
                'price_eur': Decimal('20.00'),
                'price_ron': Decimal('100.00'),
                'description': 'Pentru utilizatori activi - 25 credite cu 25% bonus'
            },
            {
                'name': 'Pachet VIP',
                'credits': Decimal('60.0'),
                'price_eur': Decimal('40.00'),
                'price_ron': Decimal('200.00'),
                'description': 'Pachet VIP - 60 credite cu 50% bonus'
            }
        ]
        
        for package_data in credit_packages:
            package, created = CreditPackage.objects.get_or_create(
                name=package_data['name'],
                defaults=package_data
            )
            if created:
                self.stdout.write(f'Created credit package: {package.name}')
        
        # Premium plans
        premium_plans = [
            {
                'name': 'Premium Matrimoniale',
                'plan_type': 'monthly',
                'price': Decimal('29.99'),
                'currency': 'RON',
                'credits_included': 10,
                'max_premium_listings': 5,
                'max_featured_listings': 3,
                'description': 'Plan special pentru Matrimoniale - anunțuri pe prima pagină',
                'features': [
                    'Anunțuri pe prima pagină în Matrimoniale',
                    'Profil evidențiat cu badge Premium',
                    '10 credite incluse lunar',
                    'Mesaje nelimitate',
                    'Suport prioritar',
                    'Statistici detaliate'
                ]
            },
            {
                'name': 'Premium Business',
                'plan_type': 'monthly', 
                'price': Decimal('49.99'),
                'currency': 'RON',
                'credits_included': 20,
                'max_premium_listings': 10,
                'max_featured_listings': 5,
                'description': 'Pentru afaceri - promovare maximă',
                'features': [
                    'Anunțuri pe prima pagină în toate categoriile',
                    'Logo companie în anunțuri',
                    '20 credite incluse lunar',
                    'Mesaje și apeluri nelimitate',
                    'Manager de cont dedicat',
                    'Rapoarte analitice avansate'
                ]
            }
        ]
        
        for plan_data in premium_plans:
            plan, created = PremiumPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created premium plan: {plan.name}')
        
        self.stdout.write(self.style.SUCCESS('Premium packages created successfully!'))