"""
Payment Verification Model - KES 1 verification before trial activation
"""
import uuid
from django.db import models
from django.utils import timezone


class PaymentVerification(models.Model):
    """Payment verification for trial activation"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    corporate_id = models.UUIDField(db_index=True)
    corporate_name = models.CharField(max_length=255, blank=True)
    
    # Verification details
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    verification_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.00,
        help_text="Verification amount in KES"
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment references
    payment_provider_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_receipt_number = models.CharField(max_length=255, blank=True, null=True)
    refund_provider_reference = models.CharField(max_length=255, blank=True, null=True)
    refund_receipt_number = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    provider_metadata = models.JSONField(default=dict, blank=True)
    refund_metadata = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    # Trial reference (once created)
    trial_created = models.BooleanField(default=False)
    trial_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        db_table = 'billing_payment_verification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['corporate_id', 'status']),
            models.Index(fields=['payment_provider_reference']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Verification {self.id} - {self.corporate_name} - {self.status}"
    
    def mark_as_verified(self, receipt_number: str, metadata: dict = None):
        """Mark verification as successful"""
        self.status = 'verified'
        self.payment_receipt_number = receipt_number
        self.verified_at = timezone.now()
        if metadata:
            self.provider_metadata = metadata
        self.save()
    
    def mark_as_failed(self, reason: str):
        """Mark verification as failed"""
        self.status = 'failed'
        self.failure_reason = reason
        self.save()
    
    def mark_as_refunded(self, refund_reference: str, refund_receipt: str = None, metadata: dict = None):
        """Mark verification amount as refunded"""
        self.status = 'refunded'
        self.refund_provider_reference = refund_reference
        self.refund_receipt_number = refund_receipt
        self.refunded_at = timezone.now()
        if metadata:
            self.refund_metadata = metadata
        self.save()
    
    def is_expired(self) -> bool:
        """Check if verification has expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    def can_create_trial(self) -> bool:
        """Check if trial can be created"""
        return self.status == 'refunded' and not self.trial_created
