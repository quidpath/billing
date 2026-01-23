"""
Subscription models for customer subscriptions
"""
from django.db import models
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from .plan import BaseModel, Plan


class Subscription(BaseModel):
    """
    Customer subscription to a plan
    """
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    # Corporate/Organization (reference to ERP)
    corporate_id = models.UUIDField()  # Reference to Corporate in ERP
    corporate_name = models.CharField(max_length=255, blank=True)  # Denormalized for convenience
    
    # Plan
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Dates
    trial_start_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)
    
    # Pricing
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    additional_users = models.IntegerField(default=0)
    additional_user_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    
    # Promotion applied
    promotion = models.ForeignKey('Promotion', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    next_billing_date = models.DateField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        indexes = [
            models.Index(fields=['corporate_id', 'status']),
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['trial_end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.corporate_name} - {self.plan.name} ({self.status})"
    
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == 'trial'
    
    def is_trial_expired(self) -> bool:
        """Check if trial has expired"""
        if not self.trial_end_date:
            return False
        return timezone.now().date() > self.trial_end_date
    
    def days_remaining_in_trial(self) -> int:
        """Get days remaining in trial"""
        if not self.trial_end_date:
            return 0
        remaining = (self.trial_end_date - timezone.now().date()).days
        return max(0, remaining)
    
    def activate(self):
        """Activate subscription after trial"""
        self.status = 'active'
        self.start_date = timezone.now().date()
        # Calculate end date based on billing cycle
        if self.billing_cycle == 'monthly':
            self.end_date = self.start_date + timedelta(days=30)
        elif self.billing_cycle == 'quarterly':
            self.end_date = self.start_date + timedelta(days=90)
        elif self.billing_cycle == 'yearly':
            self.end_date = self.start_date + timedelta(days=365)
        self.next_billing_date = self.end_date
        self.save()
    
    def cancel(self, reason: str = ""):
        """Cancel subscription"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.cancelled_reason = reason
        self.auto_renew = False
        self.save()


class SubscriptionHistory(BaseModel):
    """
    History of subscription changes
    """
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)  # created, activated, cancelled, renewed, etc.
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Subscription History"
        verbose_name_plural = "Subscription Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subscription.corporate_name} - {self.action}"








