"""
Plan service: database access for plans.
"""

from typing import List, Optional

from ..models import Plan


class PlanService:
    """Database access for plans."""

    @staticmethod
    def get_active_plans() -> List[Plan]:
        return list(Plan.objects.filter(is_active=True).order_by("price_monthly"))

    @staticmethod
    def get_plan_by_id(plan_id, active_only=True) -> Optional[Plan]:
        qs = Plan.objects.filter(id=plan_id)
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.first()
