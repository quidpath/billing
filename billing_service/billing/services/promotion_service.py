"""
Promotion service for managing offers and discounts
"""
from decimal import Decimal
from typing import Optional, Dict

from ..models.promotion import Promotion, PromotionUsage


class PromotionService:
    """Service for managing promotions"""
    
    @staticmethod
    def get_promotion_by_code(code: str) -> Optional[Promotion]:
        """Get promotion by code"""
        return Promotion.objects.filter(code=code.upper(), is_active=True).first()
    
    @staticmethod
    def apply_promotion(
        promotion_code: str,
        corporate_id: str,
        amount: Decimal,
        plan_tier: str
    ) -> Dict:
        """Apply promotion code to a purchase"""
        promotion = PromotionService.get_promotion_by_code(promotion_code)
        
        if not promotion:
            return {
                'success': False,
                'discount_amount': Decimal('0.00'),
                'message': 'Invalid promotion code',
            }
        
        if not promotion.is_valid():
            return {
                'success': False,
                'discount_amount': Decimal('0.00'),
                'message': 'Promotion code is expired or inactive',
            }
        
        if promotion.applicable_plans and plan_tier not in promotion.applicable_plans:
            return {
                'success': False,
                'discount_amount': Decimal('0.00'),
                'message': f'Promotion code not applicable to {plan_tier} plan',
            }
        
        if promotion.min_purchase_amount and amount < promotion.min_purchase_amount:
            return {
                'success': False,
                'discount_amount': Decimal('0.00'),
                'message': f'Minimum purchase amount of {promotion.min_purchase_amount} KES required',
            }
        
        if not promotion.can_be_used_by_customer(corporate_id):
            return {
                'success': False,
                'discount_amount': Decimal('0.00'),
                'message': 'Promotion code usage limit reached',
            }
        
        discount_amount = promotion.calculate_discount(amount)
        
        return {
            'success': True,
            'discount_amount': discount_amount,
            'promotion': promotion,
            'message': f'Promotion applied: {discount_amount} KES discount',
        }








