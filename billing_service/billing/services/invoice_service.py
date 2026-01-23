"""
Invoice service for generating invoices
"""
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from typing import Optional
import logging

from ..models.invoice import Invoice, InvoiceLineItem
from ..models.subscription import Subscription
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for managing invoices"""
    
    @staticmethod
    def create_invoice_for_subscription(
        subscription: Subscription,
        billing_period_start: Optional = None,
        billing_period_end: Optional = None
    ) -> Invoice:
        """Create invoice for subscription billing period"""
        invoice_number = Invoice.generate_invoice_number()
        
        if not billing_period_start:
            billing_period_start = subscription.start_date
        if not billing_period_end:
            billing_period_end = subscription.end_date
        
        due_date = timezone.now().date() + timedelta(days=7)
        
        invoice = Invoice.objects.create(
            corporate_id=subscription.corporate_id,
            corporate_name=subscription.corporate_name,
            subscription=subscription,
            invoice_number=invoice_number,
            status='pending',
            subtotal=subscription.subtotal,
            discount_amount=subscription.discount_amount,
            tax_amount=subscription.tax_amount,
            total_amount=subscription.total_amount,
            currency=subscription.currency,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            due_date=due_date,
        )
        
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=f"{subscription.plan.name} Subscription ({subscription.billing_cycle})",
            quantity=Decimal('1.00'),
            unit_price=subscription.base_price,
            total_price=subscription.base_price,
            item_type='subscription',
            item_id=subscription.id,
        )
        
        if subscription.additional_users > 0:
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=f"Additional Users ({subscription.additional_users})",
                quantity=Decimal(str(subscription.additional_users)),
                unit_price=subscription.additional_user_price,
                total_price=Decimal(str(subscription.additional_users)) * subscription.additional_user_price,
                item_type='users',
            )
        
        if subscription.discount_amount > 0:
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=f"Discount ({subscription.promotion.code if subscription.promotion else 'Promotion'})",
                quantity=Decimal('1.00'),
                unit_price=-subscription.discount_amount,
                total_price=-subscription.discount_amount,
                item_type='discount',
            )
        
        if subscription.tax_amount > 0:
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description="VAT (16%)",
                quantity=Decimal('1.00'),
                unit_price=subscription.tax_amount,
                total_price=subscription.tax_amount,
                item_type='tax',
            )
        
        # Send invoice notification
        try:
            # Get corporate email from OrgAuth (would need to be passed or fetched)
            # For now, we'll log it
            logger.info(f"Invoice {invoice.invoice_number} created for corporate {invoice.corporate_id}")
            # TODO: Fetch corporate email and send notification
            # NotificationService.send_invoice_created_notification(invoice, corporate_email)
        except Exception as e:
            logger.error(f"Error sending invoice notification: {str(e)}")
        
        return invoice
    
    @staticmethod
    def get_corporate_invoices(corporate_id: str, limit: int = 50) -> list:
        """Get invoices for corporate"""
        return list(Invoice.objects.filter(
            corporate_id=corporate_id
        ).order_by('-created_at')[:limit])
    
    @staticmethod
    def get_unpaid_invoices(corporate_id: str) -> list:
        """Get unpaid invoices for corporate"""
        return list(Invoice.objects.filter(
            corporate_id=corporate_id,
            status__in=['pending', 'overdue']
        ).order_by('-due_date'))





