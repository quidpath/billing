"""
Payment models for processing payments
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone

from .invoice import Invoice
from .plan import BaseModel


class Payment(BaseModel):
    """
    Payment records for invoices
    Supports both individual and organization payments
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHODS = [
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
        ("mobile_money", "Mobile Money"),
        ("ussd", "USSD"),
        ("other", "Other"),
    ]

    PROVIDERS = [
        ("paystack", "Paystack"),
    ]

    PAYMENT_TYPES = [
        ("individual", "Individual"),
        ("organization", "Organization"),
    ]

    # Payment Type
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPES,
        default="organization"
    )

    # Corporate/Organization or Individual User
    corporate_id = models.UUIDField()
    corporate_name = models.CharField(max_length=255, blank=True)

    # Subscription (optional - for subscription payments)
    subscription = models.ForeignKey(
        "Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscription_payments",
    )

    # Invoice
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    # Amount
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="KES")

    # Payment Method
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    provider = models.CharField(max_length=50, choices=PROVIDERS, default="paystack")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Provider References
    provider_reference = models.CharField(
        max_length=255, blank=True, null=True
    )  # Transaction ID from provider
    provider_metadata = models.JSONField(
        default=dict, blank=True
    )  # Full response from provider

    # M-Pesa specific fields
    mpesa_checkout_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_merchant_request_id = models.CharField(max_length=255, blank=True, null=True)
    mpesa_receipt_number = models.CharField(max_length=255, blank=True, null=True)
    mpesa_transaction_date = models.DateTimeField(blank=True, null=True)
    
    # Idempotency
    idempotency_key = models.CharField(max_length=255, blank=True, null=True, unique=True)

    # Payment Details
    paid_at = models.DateTimeField(null=True, blank=True)
    receipt_pdf_url = models.URLField(blank=True, null=True)

    # Customer Details (for payment processing)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["corporate_id", "status"]),
            models.Index(fields=["payment_type", "status"]),
            models.Index(fields=["invoice", "status"]),
            models.Index(fields=["provider_reference"]),
            models.Index(fields=["mpesa_checkout_request_id"]),
            models.Index(fields=["idempotency_key"]),
            models.Index(fields=["payment_method", "status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.corporate_name} - {self.amount} {self.currency} ({self.status})"

    def mark_as_success(self, provider_reference: str, metadata: dict = None):
        """Mark payment as successful"""
        self.status = "success"
        self.paid_at = timezone.now()
        self.provider_reference = provider_reference
        if metadata:
            self.provider_metadata = {**self.provider_metadata, **metadata}
        self.save()

        # Update invoice if exists
        if self.invoice:
            self.invoice.mark_as_paid(provider_reference, self.provider)

    def mark_as_failed(self, reason: str = ""):
        """Mark payment as failed"""
        self.status = "failed"
        if reason:
            self.metadata["failure_reason"] = reason
        self.save()


class PaymentMethod(BaseModel):
    """
    Saved payment methods for customers
    """

    METHOD_TYPES = [
        ("card", "Card"),
        ("mobile_money", "Mobile Money"),
        ("bank_account", "Bank Account"),
    ]

    corporate_id = models.UUIDField()
    method_type = models.CharField(max_length=50, choices=METHOD_TYPES)
    is_default = models.BooleanField(default=False)

    # Card Details (tokenized)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(
        max_length=50, blank=True, null=True
    )  # visa, mastercard
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)  # Provider token

    # Mobile Money Details
    mobile_money_phone = models.CharField(max_length=20, blank=True, null=True)

    # Bank Account Details
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)

    # Provider
    provider = models.CharField(max_length=50, default="paystack")
    provider_token = models.CharField(max_length=255, blank=True, null=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        indexes = [
            models.Index(fields=["corporate_id", "is_default"]),
        ]

    def __str__(self):
        if self.method_type == "card" and self.card_last4:
            return f"Card ending in {self.card_last4}"
        elif self.method_type == "mobile_money" and self.mobile_money_phone:
            return f"Mobile Money {self.mobile_money_phone}"
        elif self.method_type == "bank_account" and self.bank_name:
            return f"{self.bank_name} Account"
        return f"{self.get_method_type_display()}"
