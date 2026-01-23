"""
Promotion models for offers and discounts
"""
from django.db import models
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

from .plan import BaseModel


class Promotion(BaseModel):
    """
    Promotional offers and discounts
    """
    PROMOTION_TYPES = [
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        ('free_trial_extension', 'Free Trial Extension'),
        ('free_module', 'Free Module'),
        ('free_users', 'Free Additional Users'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)  # Promo code
    description = models.TextField(blank=True)
    promotion_type = models.CharField(max_length=50, choices=PROMOTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Discount Details
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # e.g., 20.00 for 20%
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Fixed amount in KES
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Cap for percentage discounts
    
    # Eligibility
    applicable_plans = models.JSONField(default=list, blank=True)  # List of plan tiers: ['starter', 'professional']
    min_purchase_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Usage Limits
    max_uses = models.IntegerField(null=True, blank=True)  # null = unlimited
    max_uses_per_customer = models.IntegerField(default=1)  # How many times one customer can use
    current_uses = models.IntegerField(default=0)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Special Offers
    free_trial_days = models.IntegerField(null=True, blank=True)  # Additional trial days
    free_modules = models.JSONField(default=list, blank=True)  # List of module types to give free
    free_users = models.IntegerField(default=0)  # Free additional users
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['status', 'start_date', 'end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def is_valid(self) -> bool:
        """Check if promotion is currently valid"""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.is_active and
            self.start_date <= now <= self.end_date and
            (self.max_uses is None or self.current_uses < self.max_uses)
        )
    
    def can_be_used_by_customer(self, corporate_id: str) -> bool:
        """Check if customer can use this promotion"""
        if not self.is_valid():
            return False
        
        # Check usage per customer
        usage_count = PromotionUsage.objects.filter(
            promotion=self,
            corporate_id=corporate_id
        ).count()
        
        return usage_count < self.max_uses_per_customer
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """Calculate discount amount for given purchase amount"""
        if not self.is_valid():
            return Decimal('0.00')
        
        if self.promotion_type == 'percentage':
            discount = amount * (self.discount_percentage / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        elif self.promotion_type == 'fixed_amount':
            return min(self.discount_amount, amount)
        
        return Decimal('0.00')


class PromotionUsage(BaseModel):
    """
    Track promotion usage by customers
    """
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='usages')
    corporate_id = models.UUIDField()
    subscription = models.ForeignKey('Subscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='promotion_usages')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Promotion Usage"
        verbose_name_plural = "Promotion Usages"
        indexes = [
            models.Index(fields=['promotion', 'corporate_id']),
        ]
    
    def __str__(self):
        return f"{self.promotion.code} used by {self.corporate_id}"








