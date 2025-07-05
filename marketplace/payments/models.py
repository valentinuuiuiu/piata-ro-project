

from django.db import models
from django.contrib.auth import get_user_model
from marketplace.models import Listing

User = get_user_model()

class EscrowPayment(models.Model):
    """Manages escrow payments between buyers and sellers"""
    
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('funded', 'Funded'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
        ('resolved', 'Resolved')
    )
    
    DISPUTE_REASONS = (
        ('item_not_received', 'Item Not Received'),
        ('item_not_as_described', 'Item Not As Described'),
        ('unauthorized_transaction', 'Unauthorized Transaction'),
        ('other', 'Other')
    )

    listing = models.ForeignKey(Listing, on_delete=models.PROTECT)
    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='escrow_buys')
    seller = models.ForeignKey(User, on_delete=models.PROTECT, related_name='escrow_sales')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='created')
    payment_intent_id = models.CharField(max_length=100)
    dispute_reason = models.CharField(max_length=25, choices=DISPUTE_REASONS, blank=True, null=True)
    dispute_description = models.TextField(blank=True, null=True)
    dispute_evidence = models.FileField(upload_to='disputes/', blank=True, null=True)
    dispute_resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Escrow Payment'
        verbose_name_plural = 'Escrow Payments'

    def __str__(self):
        return f"Escrow #{self.id} - {self.status}"

