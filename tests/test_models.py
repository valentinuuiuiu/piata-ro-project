import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from marketplace.models import (
    Category, Listing, UserProfile, CreditTransaction,
    Payment, CreditPackage, Message, Favorite, ListingReport
)
from decimal import Decimal


class TestCategoryModel(TestCase):
    """Test Category model functionality"""

    def setUp(self):
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_category_creation(self):
        """Test category basic creation"""
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.category.slug, 'test-category')
        self.assertIsNotNone(self.category.pk)

    def test_auto_slug_generation(self):
        """Test automatic slug generation"""
        category = Category.objects.create(name='Test Category 2')
        self.assertEqual(category.slug, 'test-category-2')

    def test_category_str_method(self):
        """Test string representation"""
        self.assertEqual(str(self.category), 'Test Category')


class TestUserProfileModel(TestCase):
    """Test UserProfile model functionality"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.profile = UserProfile.objects.create(
            user=self.user,
            credits_balance=Decimal('10.00')
        )

    def test_profile_creation(self):
        """Test user profile creation"""
        self.assertEqual(self.profile.credits_balance, Decimal('10.00'))
        self.assertEqual(self.profile.user, self.user)

    def test_credits_deduct(self):
        """Test credit deduction"""
        result = self.profile.deduct_credits(Decimal('5.00'))
        self.assertTrue(result)
        self.assertEqual(self.profile.credits_balance, Decimal('5.00'))

    def test_insufficient_credits(self):
        """Test insufficient credits handling"""
        result = self.profile.deduct_credits(Decimal('15.00'))
        self.assertFalse(result)
        self.assertEqual(self.profile.credits_balance, Decimal('10.00'))


class TestListingModel(TestCase):
    """Test Listing model functionality"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.listing = Listing.objects.create(
            title='iPhone 14',
            description='Latest iPhone',
            price=Decimal('2000.00'),
            currency='RON',
            location='București',
            user=self.user,
            category=self.category,
            status='active'
        )

    def test_listing_creation(self):
        """Test listing creation"""
        self.assertEqual(self.listing.title, 'iPhone 14')
        self.assertEqual(self.listing.status, 'active')
        self.assertEqual(self.listing.price, Decimal('2000.00'))

    def test_main_image_no_images(self):
        """Test main_image property with no images"""
        self.assertIsNone(self.listing.main_image)


class TestCreditPackageModel(TestCase):
    """Test CreditPackage model functionality"""

    def setUp(self):
        self.package = CreditPackage.objects.create(
            name='Basic Package',
            base_credits=10,
            bonus_credits=2,
            price_eur=Decimal('5.00'),
            price_ron=Decimal('25.00'),
            is_active=True
        )

    def test_total_credits_calculation(self):
        """Test total credits calculation"""
        self.assertEqual(self.package.total_credits, 12)  # 10 base + 2 bonus

    def test_effective_price_calculation(self):
        """Test price per credit calculation"""
        euro_price = self.package.get_effective_price('EUR')
        self.assertEqual(euro_price, Decimal('5.00') / Decimal('12'))


class TestPaymentModel(TestCase):
    """Test Payment model functionality"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.payment = Payment.objects.create(
            user=self.user,
            payment_type='credits',
            amount=Decimal('25.00'),
            currency='RON',
            status='pending'
        )

    def test_payment_creation(self):
        """Test payment creation"""
        self.assertEqual(self.payment.payment_type, 'credits')
        self.assertEqual(self.payment.status, 'pending')
        self.assertIsNotNone(self.payment.stripe_payment_intent_id)


class TestMessageModel(TestCase):
    """Test Message model functionality"""

    def setUp(self):
        self.sender = User.objects.create_user('sender', 'sender@example.com', 'password123')
        self.receiver = User.objects.create_user('receiver', 'receiver@example.com', 'password123')
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content='This is a test message.'
        )

    def test_message_creation(self):
        """Test message creation"""
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.receiver, self.receiver)
        self.assertEqual(self.message.content, 'This is a test message.')
        self.assertFalse(self.message.is_read)

    def test_message_str(self):
        """Test string representation"""
        expected = f"Message from {self.sender.username} to {self.receiver.username}"
        self.assertEqual(str(self.message), expected)


class TestFavoriteModel(TestCase):
    """Test Favorite model functionality"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.listing = Listing.objects.create(
            title='Test Item', description='Test', price=Decimal('100.00'),
            location='Test', user=self.user, category=self.category
        )

    def test_favorite_creation(self):
        """Test favorite creation (unique constraint)"""
        favorite = Favorite.objects.create(
            user=self.user,
            listing=self.listing
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.listing, self.listing)

    def test_duplicate_favorite_prevention(self):
        """Test that duplicate favorites are not allowed"""
        Favorite.objects.create(user=self.user, listing=self.listing)

        with self.assertRaises(Exception):  # This should raise IntegrityError
            Favorite.objects.create(user=self.user, listing=self.listing)


class TestCreditTransactionModel(TestCase):
    """Test CreditTransaction model functionality"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.transaction = CreditTransaction.objects.create(
            user=self.user,
            transaction_type='purchase',
            amount=5,
            description='Test purchase'
        )

    def test_transaction_creation(self):
        """Test transaction creation"""
        self.assertEqual(self.transaction.transaction_type, 'purchase')
        self.assertEqual(self.transaction.amount, 5)
        self.assertEqual(self.transaction.user, self.user)


class TestListingReportModel(TestCase):
    """Test ListingReport model functionality"""

    def setUp(self):
        self.reporter = User.objects.create_user('reporter', 'reporter@example.com', 'password123')
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.listing = Listing.objects.create(
            title='Report Test', description='Test', price=Decimal('100.00'),
            location='Test', user=self.reporter, category=self.category
        )

    def test_report_creation(self):
        """Test report creation"""
        report = ListingReport.objects.create(
            listing=self.listing,
            reporter=self.reporter,
            reason='fake',
            comment='This seems suspicious'
        )
        self.assertEqual(report.reason, 'fake')
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.listing, self.listing)
        self.assertEqual(report.status, 'pending')
