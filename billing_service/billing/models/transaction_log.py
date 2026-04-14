"""
Transaction Logging Models for Billing Service
Tracks all actions and transactions in the billing microservice
"""
from django.db import models
from django.contrib.postgres.fields import JSONField as PostgresJSONField
from decimal import Decimal


class BaseModel(models.Model):
    """Base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=models.uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class State(BaseModel):
    """Represents a global state e.g. Active, Completed, Failed, Pending"""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "State"
        verbose_name_plural = "States"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def bootstrap_defaults(cls):
        """Ensure default states always exist"""
        defaults = ["Active", "Completed", "Failed", "Pending", "Processing", "Cancelled"]
        for name in defaults:
            cls.objects.get_or_create(
                name=name, 
                defaults={"description": f"{name} state"}
            )


class TransactionType(BaseModel):
    """High-level transaction type for billing operations"""
    
    name = models.CharField(max_length=100, unique=True)
    simple_name = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)  # payment, subscription, invoice, etc.
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Transaction Type"
        verbose_name_plural = "Transaction Types"
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    @classmethod
    def bootstrap_defaults(cls):
        """Default billing transaction types"""
        defaults = [
            # Payment transactions
            {"name": "PAYMENT_INITIATED", "category": "payment", "description": "Payment initiation started"},
            {"name": "PAYMENT_SUCCESS", "category": "payment", "description": "Payment completed successfully"},
            {"name": "PAYMENT_FAILED", "category": "payment", "description": "Payment failed"},
            {"name": "PAYMENT_WEBHOOK_RECEIVED", "category": "payment", "description": "Payment webhook received from provider"},
            {"name": "PAYMENT_VERIFIED", "category": "payment", "description": "Payment verification completed"},
            
            # Invoice transactions
            {"name": "INVOICE_CREATED", "category": "invoice", "description": "Invoice created"},
            {"name": "INVOICE_PAID", "category": "invoice", "description": "Invoice marked as paid"},
            {"name": "INVOICE_CANCELLED", "category": "invoice", "description": "Invoice cancelled"},
            {"name": "INVOICE_OVERDUE", "category": "invoice", "description": "Invoice marked as overdue"},
            
            # Subscription transactions
            {"name": "SUBSCRIPTION_CREATED", "category": "subscription", "description": "Subscription created"},
            {"name": "SUBSCRIPTION_ACTIVATED", "category": "subscription", "description": "Subscription activated"},
            {"name": "SUBSCRIPTION_CANCELLED", "category": "subscription", "description": "Subscription cancelled"},
            {"name": "SUBSCRIPTION_EXPIRED", "category": "subscription", "description": "Subscription expired"},
            {"name": "SUBSCRIPTION_UPGRADED", "category": "subscription", "description": "Subscription upgraded"},
            {"name": "SUBSCRIPTION_DOWNGRADED", "category": "subscription", "description": "Subscription downgraded"},
            
            # Trial transactions
            {"name": "TRIAL_CREATED", "category": "trial", "description": "Trial created"},
            {"name": "TRIAL_ACTIVATED", "category": "trial", "description": "Trial activated"},
            {"name": "TRIAL_EXPIRED", "category": "trial", "description": "Trial expired"},
            
            # Verification transactions
            {"name": "VERIFICATION_INITIATED", "category": "verification", "description": "Payment verification initiated"},
            {"name": "VERIFICATION_SUCCESS", "category": "verification", "description": "Payment verification successful"},
            {"name": "VERIFICATION_FAILED", "category": "verification", "description": "Payment verification failed"},
            
            # Webhook transactions
            {"name": "WEBHOOK_SENT", "category": "webhook", "description": "Webhook sent to main backend"},
            {"name": "WEBHOOK_FAILED", "category": "webhook", "description": "Webhook delivery failed"},
            
            # Access control
            {"name": "ACCESS_CHECK", "category": "access", "description": "Access check performed"},
            {"name": "ACCESS_GRANTED", "category": "access", "description": "Access granted"},
            {"name": "ACCESS_DENIED", "category": "access", "description": "Access denied"},
        ]
        
        for item in defaults:
            cls.objects.get_or_create(
                name=item["name"],
                defaults={
                    "simple_name": item["name"],
                    "category": item.get("category", "general"),
                    "description": item.get("description", "")
                }
            )


class BillingTransaction(BaseModel):
    """
    Transaction log for all billing operations
    Tracks every action in the billing microservice
    """
    
    reference = models.CharField(max_length=255, unique=True, db_index=True)
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.PROTECT)
    
    # Corporate/Organization context
    corporate_id = models.UUIDField(null=True, blank=True, db_index=True)
    corporate_name = models.CharField(max_length=255, blank=True, null=True)
    
    # User context (if available)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_email = models.EmailField(blank=True, null=True)
    
    # Related entities
    payment_id = models.UUIDField(null=True, blank=True, db_index=True)
    invoice_id = models.UUIDField(null=True, blank=True, db_index=True)
    subscription_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Transaction details
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="KES")
    
    # Status and response
    state = models.ForeignKey(State, on_delete=models.PROTECT)
    message = models.TextField(blank=True, null=True)
    response_code = models.CharField(max_length=50, blank=True, null=True)
    response_message = models.TextField(blank=True, null=True)
    
    # Request context
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Provider details (Paystack, M-Pesa, etc.)
    provider = models.CharField(max_length=50, blank=True, null=True)
    provider_reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Webhook/notification response
    webhook_response = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Billing Transaction"
        verbose_name_plural = "Billing Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["corporate_id", "transaction_type"]),
            models.Index(fields=["payment_id", "state"]),
            models.Index(fields=["invoice_id", "state"]),
            models.Index(fields=["subscription_id", "state"]),
            models.Index(fields=["provider_reference"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.reference} - {self.transaction_type.name} - {self.state.name}"


class AuditLog(BaseModel):
    """
    Audit log for administrative actions and system events
    """
    
    ACTION_TYPES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("access", "Access"),
        ("webhook", "Webhook"),
        ("admin", "Admin Action"),
        ("system", "System Event"),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_type = models.CharField(max_length=50)  # payment, invoice, subscription, etc.
    entity_id = models.UUIDField(null=True, blank=True)
    
    # Who performed the action
    user_id = models.UUIDField(null=True, blank=True)
    user_email = models.EmailField(blank=True, null=True)
    corporate_id = models.UUIDField(null=True, blank=True)
    
    # What changed
    action_description = models.TextField()
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Request context
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["corporate_id", "action_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action_type} - {self.entity_type} - {self.created_at}"
