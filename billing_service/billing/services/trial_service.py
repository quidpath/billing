"""
Trial service for managing 30-day free trials
"""

from datetime import timedelta
from typing import Optional

from django.utils import timezone

from ..models.plan import Plan
from ..models.trial import Trial


class TrialService:
    """Service for managing free trials"""

    @staticmethod
    def create_trial_for_corporate(
        corporate_id: str, corporate_name: str = "", plan_tier: str = "starter",
        phone_number: str = "",
    ) -> Trial:
        """Create a 30-day free trial for a new corporate"""
        existing_trial = Trial.objects.filter(corporate_id=corporate_id).first()
        if existing_trial:
            # Update phone number if provided and not already set
            if phone_number and not existing_trial.metadata.get("phone_number"):
                existing_trial.metadata["phone_number"] = phone_number
                existing_trial.save(update_fields=["metadata"])
            return existing_trial

        plan = Plan.objects.filter(tier=plan_tier, is_active=True).first()
        if not plan:
            plan = Plan.objects.filter(tier="starter", is_active=True).first()

        if not plan:
            raise ValueError("No active plan found for trial")

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30)

        metadata = {}
        if phone_number:
            metadata["phone_number"] = phone_number

        trial = Trial.objects.create(
            corporate_id=corporate_id,
            corporate_name=corporate_name,
            plan=plan,
            status="active",
            start_date=start_date,
            end_date=end_date,
            included_users=plan.included_users,
            metadata=metadata,
        )

        return trial

    @staticmethod
    def get_active_trial(corporate_id: str) -> Optional[Trial]:
        """Get active trial for corporate"""
        return Trial.objects.filter(corporate_id=corporate_id, status="active").first()

    @staticmethod
    def check_trial_status(corporate_id: str) -> dict:
        """Check trial status and return details"""
        trial = TrialService.get_active_trial(corporate_id)

        if not trial:
            return {"has_trial": False, "trial": None}

        days_remaining = trial.days_remaining()
        is_expired = trial.is_expired()

        if is_expired and trial.status == "active":
            trial.expire()
            trial.status = "expired"

        return {
            "has_trial": True,
            "trial": {
                "id": str(trial.id),
                "status": trial.status,
                "plan_name": trial.plan.name,
                "plan_tier": trial.plan.tier,
                "start_date": trial.start_date.isoformat(),
                "end_date": trial.end_date.isoformat(),
                "days_remaining": days_remaining,
                "is_active": trial.is_active(),
                "is_expired": is_expired,
                "included_users": trial.included_users,
                "phone_number": trial.metadata.get("phone_number", ""),
            },
        }
