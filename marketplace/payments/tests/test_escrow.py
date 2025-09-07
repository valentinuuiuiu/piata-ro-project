

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from marketplace.models import Listing, Category
from ..models import EscrowPayment

User = get_user_model()

# @pytest.mark.django_db
# class TestEscrow:
#     @pytest.fixture
#     def client(self):
#         return APIClient()

#     @pytest.fixture
#     def seller(self):
#         import time
#         return User.objects.create_user(
#             username=f'seller_{int(time.time())}',
#             email='seller@test.com',
#             password='testpass123'
#         )

#     @pytest.fixture
#     def buyer(self):
#         import time
#         time.sleep(1)
#         return User.objects.create_user(
#             username=f'buyer_{int(time.time())}',
#             email='buyer@test.com',
#             password='testpass123'
#         )

#     @pytest.fixture
#     def category(self):
#         return Category.objects.create(name='Test Category', slug='test-category')

#     @pytest.fixture
#     def listing(self, seller, category):
#         return Listing.objects.create(
#             user=seller,
#             title='Test Listing',
#             price=100.00,
#             description='Test description',
#             category=category
#         )

#     def test_create_escrow(self, client, listing, buyer):
#         client.force_authenticate(user=buyer)
#         response = client.post(
#             f'/api/payments/escrow/create/{listing.id}/'
#         )
#         assert response.status_code == status.HTTP_200_OK
#         assert EscrowPayment.objects.exists()

#     def test_release_funds(self, client, listing, buyer, seller):
#         escrow = EscrowPayment.objects.create(
#             listing=listing,
#             buyer=buyer,
#             seller=seller,
#             amount=listing.price,
#             status='funded'
#         )
#         client.force_authenticate(user=seller)
#         response = client.post(
#             f'/api/payments/escrow/release/{escrow.id}/'
#         )
#         assert response.status_code == status.HTTP_200_OK
#         escrow.refresh_from_db()
#         assert escrow.status == 'released'

#     def test_refund_funds(self, client, listing, buyer, seller):
#         escrow = EscrowPayment.objects.create(
#             listing=listing,
#             buyer=buyer,
#             seller=seller,
#             amount=listing.price,
#             status='funded'
#         )
#         client.force_authenticate(user=buyer)
#         response = client.post(
#             f'/api/payments/escrow/refund/{escrow.id}/'
#         )
#         assert response.status_code == status.HTTP_200_OK
#         escrow.refresh_from_db()
#         assert escrow.status == 'refunded'

#     def test_unauthorized_access(self, client, listing, buyer, seller):
#         escrow = EscrowPayment.objects.create(
#             listing=listing,
#             buyer=buyer,
#             seller=seller,
#             amount=listing.price,
#             status='funded'
#         )
#         client.force_authenticate(user=buyer)
#         response = client.post(
#             f'/api/payments/escrow/release/{escrow.id}/'
#         )
#         assert response.status_code == status.HTTP_403_FORBIDDEN

