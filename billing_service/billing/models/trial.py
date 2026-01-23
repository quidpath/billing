"""
Trial models for 30-day free trial
"""
from django.db import models
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from .plan import BaseModel, Plan


class Trial(BaseModel):
    """
    30-day free trial for new customers
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Corporate/Organization
    corporate_id = models.UUIDField(unique=True)  # One trial per corporate
    corporate_name = models.CharField(max_length=255, blank=True)
    
    # Plan
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='trials')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()  # start_date + 30 days
    converted_at = models.DateTimeField(null=True, blank=True)
    
    # Trial Features
    included_users = models.IntegerField(default=3)
    included_modules = models.JSONField(default=list, blank=True)  # Modules available in trial
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Trial"
        verbose_name_plural = "Trials"
        indexes = [
            models.Index(fields=['corporate_id', 'status']),
            models.Index(fields=['status', 'end_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.corporate_name} - Trial ({self.status})"
    
    @classmethod
    def create_trial(cls, corporate_id: str, corporate_name: str = "", plan_tier: str = 'starter'):
        """Create a 30-day free trial"""
        # Get starter plan by default
        plan = Plan.objects.filter(tier=plan_tier, is_active=True).first()
        if not plan:
            plan = Plan.objects.filter(tier='starter', is_active=True).first()
        
        if not plan:
            raise ValueError("No active plan found for trial")
        
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30)
        
        trial = cls.objects.create(
            corporate_id=corporate_id,
            corporate_name=corporate_name,
            plan=plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            included_users=plan.included_users,
        )
        
        return trial
    
    def is_active(self) -> bool:
        """Check if trial is currently active"""
        return (
            self.status == 'active' and
            timezone.now().date() <= self.end_date
        )
    
    def is_expired(self) -> bool:
        """Check if trial has expired"""
        return (
            self.status == 'active' and
            timezone.now().date() > self.end_date
        )
    
    def days_remaining(self) -> int:
        """Get days remaining in trial"""
        if self.status != 'active':
            return 0
        remaining = (self.end_date - timezone.now().date()).days
        return max(0, remaining)
    
    def convert_to_subscription(self, billing_cycle: str = 'monthly'):
        """Convert trial to paid subscription"""
        from .subscription import Subscription
        
        if self.status != 'active':
            raise ValueError("Trial is not active")
        
        # Create subscription
        subscription = Subscription.objects.create(
            corporate_id=self.corporate_id,
            corporate_name=self.corporate_name,
            plan=self.plan,
            billing_cycle=billing_cycle,
            status='active',
            trial_start_date=self.start_date,
            trial_end_date=self.end_date,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30 if billing_cycle == 'monthly' else 90 if billing_cycle == 'quarterly' else 365),
            base_price=self.plan.get_price_for_cycle(billing_cycle),
            subtotal=self.plan.get_price_for_cycle(billing_cycle),
            total_amount=self.plan.get_price_for_cycle(billing_cycle),
            currency='KES',
        )
        
        # Mark trial as converted
        self.status = 'converted'
        self.converted_at = timezone.now()
        self.save()
        
        return subscription
    
    def expire(self):
        """Mark trial as expired"""
        self.status = 'expired'
        self.save()








