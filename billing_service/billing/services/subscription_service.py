"""
Subscription service for managing subscriptions
"""

from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ..models.plan import Plan
from ..models.promotion import Promotion
from ..models.subscription import Subscription, SubscriptionHistory
from .promotion_service import PromotionService


class SubscriptionService:
    """Service for managing subscriptions"""

    @staticmethod
    def create_subscription(
        corporate_id: str,
        corporate_name: str,
        plan_tier: str,
        billing_cycle: str = "monthly",
        additional_users: int = 0,
        promotion_code: Optional[str] = None,
        trial_start_date: Optional = None,
        trial_end_date: Optional = None,
    ) -> Subscription:
        """Create a new subscription"""
        plan = Plan.objects.filter(tier=plan_tier, is_active=True).first()
        if not plan:
            raise ValueError(f"Plan tier '{plan_tier}' not found or inactive")

        base_price = plan.get_price_for_cycle(billing_cycle)
        additional_user_cost = (
            Decimal(str(additional_users)) * plan.additional_user_price
        )
        subtotal = base_price + additional_user_cost

        discount_amount = Decimal("0.00")
        promotion = None
        if promotion_code:
            promotion_result = PromotionService.apply_promotion(
                promotion_code=promotion_code,
                corporate_id=corporate_id,
                amount=subtotal,
                plan_tier=plan_tier,
            )
            if promotion_result["success"]:
                discount_amount = promotion_result["discount_amount"]
                promotion = promotion_result["promotion"]

        tax_rate = Decimal("0.16")
        tax_amount = (subtotal - discount_amount) * tax_rate
        total_amount = subtotal - discount_amount + tax_amount

        start_date = timezone.now().date()
        if billing_cycle == "monthly":
            end_date = start_date + timedelta(days=30)
        elif billing_cycle == "quarterly":
            end_date = start_date + timedelta(days=90)
        elif billing_cycle == "yearly":
            end_date = start_date + timedelta(days=365)
        else:
            end_date = start_date + timedelta(days=30)

        subscription = Subscription.objects.create(
            corporate_id=corporate_id,
            corporate_name=corporate_name,
            plan=plan,
            billing_cycle=billing_cycle,
            status="active",
            trial_start_date=trial_start_date,
            trial_end_date=trial_end_date,
            start_date=start_date,
            end_date=end_date,
            base_price=base_price,
            additional_users=additional_users,
            additional_user_price=plan.additional_user_price,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency="KES",
            promotion=promotion,
            auto_renew=True,
            next_billing_date=end_date,
        )

        SubscriptionHistory.objects.create(
            subscription=subscription,
            action="created",
            new_status="active",
            description=f"Subscription created for {plan.name} plan",
        )

        return subscription

    @staticmethod
    def get_active_subscription(corporate_id: str) -> Optional[Subscription]:
        """Get active subscription for corporate"""
        return (
            Subscription.objects.filter(
                corporate_id=corporate_id, status__in=["active", "trial"]
            )
            .order_by("-created_at")
            .first()
        )
