

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from marketplace.models import Listing
from ..models import EscrowPayment

User = get_user_model()

class EscrowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            email='seller@test.com',
            password='testpass123'
        )
        self.buyer = User.objects.create_user(
            email='buyer@test.com',
            password='testpass123'
        )
        self.listing = Listing.objects.create(
            user=self.seller,
            title='Test Listing',
            price=100.00,
            description='Test description'
        )
        self.client.force_authenticate(user=self.buyer)

    def test_create_escrow(self):
        response = self.client.post(
            f'/api/payments/escrow/create/{self.listing.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(EscrowPayment.objects.exists())

    def test_release_funds(self):
        escrow = EscrowPayment.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            amount=self.listing.price,
            status='funded'
        )
        self.client.force_authenticate(user=self.seller)
        response = self.client.post(
            f'/api/payments/escrow/release/{escrow.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        escrow.refresh_from_db()
        self.assertEqual(escrow.status, 'released')

    def test_refund_funds(self):
        escrow = EscrowPayment.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            amount=self.listing.price,
            status='funded'
        )
        response = self.client.post(
            f'/api/payments/escrow/refund/{escrow.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        escrow.refresh_from_db()
        self.assertEqual(escrow.status, 'refunded')

    def test_unauthorized_access(self):
        # Test buyer cannot release funds
        escrow = EscrowPayment.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            seller=self.seller,
            amount=self.listing.price,
            status='funded'
        )
        response = self.client.post(
            f'/api/payments/escrow/release/{escrow.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

