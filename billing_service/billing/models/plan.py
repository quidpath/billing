"""
Plan models for subscription plans (Starter, Professional, Business, Enterprise)
"""

import uuid
from decimal import Decimal

from django.db import models


class BaseModel(models.Model):
    """Base model with common fields"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Plan(BaseModel):
    """
    Subscription plans: Starter, Professional, Business, Enterprise
    """

    PLAN_TIERS = [
        ("starter", "Starter"),
        ("professional", "Professional"),
        ("business", "Business"),
        ("enterprise", "Enterprise"),
    ]

    BILLING_CYCLES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    # Basic Info
    name = models.CharField(max_length=100, unique=True)  # Starter, Professional, etc.
    tier = models.CharField(max_length=50, choices=PLAN_TIERS, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # Featured on pricing page

    # Pricing (KES)
    price_monthly = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    price_quarterly = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    price_yearly = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    # Discounts for longer commitments
    quarterly_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.00")
    )
    yearly_discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("20.00")
    )

    # User Limits
    included_users = models.IntegerField(default=3)  # Users included in base price
    additional_user_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("800.00")
    )
    max_users = models.IntegerField(null=True, blank=True)  # null = unlimited

    # Feature Limits (JSON)
    limits = models.JSONField(
        default=dict, blank=True
    )  # e.g., {"invoices": 50, "storage_gb": 5}

    # Modules Included (many-to-many via PlanModule)
    # This will be handled via PlanModule model

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Plans"
        ordering = ["price_monthly"]
        indexes = [
            models.Index(fields=["tier", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} - KES {self.price_monthly}/month"

    def get_price_for_cycle(self, cycle: str) -> Decimal:
        """Get price for billing cycle with discount applied"""
        if cycle == "monthly":
            return self.price_monthly
        elif cycle == "quarterly":
            if self.price_quarterly:
                return self.price_quarterly
            # Calculate with discount
            return self.price_monthly * 3 * (1 - self.quarterly_discount_percent / 100)
        elif cycle == "yearly":
            if self.price_yearly:
                return self.price_yearly
            # Calculate with discount
            return self.price_monthly * 12 * (1 - self.yearly_discount_percent / 100)
        return self.price_monthly

    def calculate_total_price(self, cycle: str, additional_users: int = 0) -> Decimal:
        """Calculate total price including additional users"""
        base_price = self.get_price_for_cycle(cycle)
        user_cost = Decimal(str(additional_users)) * self.additional_user_price
        return base_price + user_cost


class PlanFeature(BaseModel):
    """
    Individual features that can be included in plans
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    feature_key = models.CharField(
        max_length=100, unique=True
    )  # e.g., "ai_analyses", "api_calls"
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"

    def __str__(self):
        return self.name


class PlanModule(BaseModel):
    """
    Modules that can be added to plans (CRM, HR, Manufacturing, etc.)
    """

    MODULE_TYPES = [
        ("accounting", "Accounting"),
        ("inventory", "Inventory Management"),
        ("sales", "Sales Management"),
        ("purchases", "Purchase Management"),
        ("crm", "CRM"),
        ("hr", "HR Management"),
        ("payroll", "Payroll"),
        ("project", "Project Management"),
        ("manufacturing", "Manufacturing/MRP"),
        ("ecommerce", "E-commerce"),
        ("pos", "Point of Sale"),
        ("fleet", "Fleet Management"),
        ("maintenance", "Maintenance"),
        ("quality", "Quality Control"),
        ("document", "Document Management"),
        ("bi", "BI & Analytics"),
        ("workflow", "Workflow Automation"),
        ("multicompany", "Multi-Company"),
        ("tazama_ai", "Tazama AI"),
    ]

    name = models.CharField(max_length=100)
    module_type = models.CharField(max_length=50, choices=MODULE_TYPES, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Pricing per tier (KES/month)
    price_starter = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    price_professional = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    price_business = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    price_enterprise = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    # If included in Enterprise plan
    included_in_enterprise = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Plan Module"
        verbose_name_plural = "Plan Modules"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_price_for_tier(self, tier: str) -> Decimal:
        """Get module price for plan tier"""
        price_map = {
            "starter": self.price_starter,
            "professional": self.price_professional,
            "business": self.price_business,
            "enterprise": (
                Decimal("0.00")
                if self.included_in_enterprise
                else self.price_enterprise
            ),
        }
        return price_map.get(tier, Decimal("0.00"))


class PlanModuleAssignment(BaseModel):
    """
    Many-to-many relationship between Plans and Modules
    """

    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="module_assignments"
    )
    module = models.ForeignKey(
        PlanModule, on_delete=models.CASCADE, related_name="plan_assignments"
    )
    is_included = models.BooleanField(default=False)  # If included in base plan
    is_available = models.BooleanField(default=True)  # If available as add-on

    class Meta:
        unique_together = [["plan", "module"]]
        verbose_name = "Plan Module Assignment"
        verbose_name_plural = "Plan Module Assignments"

    def __str__(self):
        status = "Included" if self.is_included else "Available"
        return f"{self.plan.name} - {self.module.name} ({status})"
