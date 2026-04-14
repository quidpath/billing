"""
Invoice models for billing
"""

from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from .plan import BaseModel
from .subscription import Subscription


class Invoice(BaseModel):
    """
    Billing invoices for subscriptions
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    # Corporate/Organization
    corporate_id = models.UUIDField()
    corporate_name = models.CharField(max_length=255, blank=True)

    # Subscription
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )

    # Invoice Details
    invoice_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Amounts
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    currency = models.CharField(max_length=3, default="KES")

    # Billing Period
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)

    # Payment Reference
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_provider = models.CharField(
        max_length=50, blank=True, null=True
    )  # paystack, etc.

    # PDF
    invoice_pdf_url = models.URLField(blank=True, null=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        indexes = [
            models.Index(fields=["corporate_id", "status"]),
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["due_date", "status"]),
            models.Index(fields=["subscription"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} - {self.corporate_name} ({self.status})"

    @classmethod
    def generate_invoice_number(cls) -> str:
        """Generate unique invoice number"""
        timestamp = timezone.now().strftime("%Y%m%d")
        # Get count of invoices today
        count = cls.objects.filter(
            invoice_number__startswith=f"INV-{timestamp}"
        ).count()
        return f"INV-{timestamp}-{count + 1:04d}"

    def mark_as_paid(self, payment_reference: str, provider: str = "paystack"):
        """Mark invoice as paid and activate subscription if exists"""
        import logging
        logger = logging.getLogger(__name__)
        
        from ..utils.transaction_logger import TransactionLogger
        
        logger.info(f"Marking invoice {self.id} ({self.invoice_number}) as paid. Current status: {self.status}")
        
        # Log invoice payment start
        TransactionLogger.log(
            transaction_type="INVOICE_PAID",
            corporate_id=str(self.corporate_id),
            corporate_name=self.corporate_name,
            invoice_id=str(self.id),
            subscription_id=str(self.subscription_id) if self.subscription_id else None,
            amount=self.total_amount,
            currency=self.currency,
            message=f"Invoice {self.invoice_number} being marked as paid",
            state_name="Processing",
            provider=provider,
            provider_reference=payment_reference,
        )
        
        self.status = "paid"
        self.paid_at = timezone.now()
        self.payment_reference = payment_reference
        self.payment_provider = provider
        self.save(update_fields=["status", "paid_at", "payment_reference", "payment_provider", "updated_at"])
        
        logger.info(f"Invoice {self.id} marked as paid successfully. New status: {self.status}")
        
        # Activate subscription if this invoice is for a subscription
        if self.subscription:
            logger.info(f"Invoice {self.id} has subscription {self.subscription.id}, current status: {self.subscription.status}")
            if self.subscription.status != "active":
                self.subscription.status = "active"
                self.subscription.save(update_fields=["status", "updated_at"])
                logger.info(f"Subscription {self.subscription.id} activated")
                
                # Log subscription activation
                TransactionLogger.log(
                    transaction_type="SUBSCRIPTION_ACTIVATED",
                    corporate_id=str(self.corporate_id),
                    corporate_name=self.corporate_name,
                    invoice_id=str(self.id),
                    subscription_id=str(self.subscription.id),
                    amount=self.total_amount,
                    currency=self.currency,
                    message=f"Subscription {self.subscription.id} activated via invoice {self.invoice_number}",
                    state_name="Completed",
                    provider=provider,
                    provider_reference=payment_reference,
                )
                
                # Send webhook to main backend
                try:
                    from ..services.webhook_service import webhook_service
                    webhook_service.send_payment_succeeded(
                        self.subscription,
                        {
                            "invoice_id": str(self.id),
                            "invoice_number": self.invoice_number,
                            "amount": float(self.total_amount),
                            "currency": self.currency,
                            "payment_reference": payment_reference,
                            "payment_provider": provider,
                            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
                        }
                    )
                    logger.info(f"Webhook sent to main backend for subscription {self.subscription.id}")
                    
                    # Log webhook sent
                    TransactionLogger.log(
                        transaction_type="WEBHOOK_SENT",
                        corporate_id=str(self.corporate_id),
                        corporate_name=self.corporate_name,
                        invoice_id=str(self.id),
                        subscription_id=str(self.subscription.id),
                        message=f"Webhook sent to main backend for subscription {self.subscription.id}",
                        state_name="Completed",
                        metadata={"event": "payment.succeeded"},
                    )
                except Exception as e:
                    logger.error(f"Failed to send webhook to main backend: {e}", exc_info=True)
                    
                    # Log webhook failure
                    TransactionLogger.log(
                        transaction_type="WEBHOOK_FAILED",
                        corporate_id=str(self.corporate_id),
                        corporate_name=self.corporate_name,
                        invoice_id=str(self.id),
                        subscription_id=str(self.subscription.id),
                        message=f"Failed to send webhook: {str(e)}",
                        state_name="Failed",
                        response_code="500",
                        response_message=str(e),
                    )
            else:
                logger.info(f"Subscription {self.subscription.id} already active")
        else:
            logger.info(f"Invoice {self.id} has no associated subscription")
        
        # Log final completion
        TransactionLogger.log(
            transaction_type="INVOICE_PAID",
            corporate_id=str(self.corporate_id),
            corporate_name=self.corporate_name,
            invoice_id=str(self.id),
            subscription_id=str(self.subscription_id) if self.subscription_id else None,
            amount=self.total_amount,
            currency=self.currency,
            message=f"Invoice {self.invoice_number} marked as paid successfully",
            state_name="Completed",
            provider=provider,
            provider_reference=payment_reference,
            response_code="200",
            response_message="Invoice marked as paid",
        )

    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return self.status == "pending" and timezone.now().date() > self.due_date


class InvoiceLineItem(BaseModel):
    """
    Line items for invoices
    """

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="line_items"
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1.00")
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Optional: Link to plan/module
    item_type = models.CharField(
        max_length=50, blank=True
    )  # subscription, module, user, etc.
    item_id = models.UUIDField(null=True, blank=True)

    class Meta:
        verbose_name = "Invoice Line Item"
        verbose_name_plural = "Invoice Line Items"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
