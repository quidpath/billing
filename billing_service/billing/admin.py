"""
Admin interface for billing models
"""

from django.contrib import admin

from .models import (Invoice, InvoiceLineItem, Payment, PaymentMethod, Plan,
                     PlanFeature, PlanModule, PlanModuleAssignment, Promotion,
                     PromotionUsage, Subscription, SubscriptionHistory, Trial,
                     State, TransactionType, BillingTransaction, AuditLog)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tier",
        "price_monthly",
        "included_users",
        "is_active",
        "is_featured",
    ]
    list_filter = ["tier", "is_active", "is_featured"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "corporate_name",
        "plan",
        "status",
        "billing_cycle",
        "total_amount",
        "start_date",
        "end_date",
    ]
    list_filter = ["status", "billing_cycle", "plan__tier"]


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ["corporate_name", "plan", "status", "start_date", "end_date"]
    list_filter = ["status", "plan__tier"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "corporate_name",
        "status",
        "total_amount",
        "due_date",
        "paid_at",
    ]
    list_filter = ["status", "currency"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "corporate_name",
        "amount",
        "currency",
        "payment_method",
        "status",
        "provider",
        "paid_at",
    ]
    list_filter = ["status", "payment_method", "provider"]


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name", "description"]


@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "simple_name", "created_at"]
    list_filter = ["category"]
    search_fields = ["name", "simple_name", "description"]


@admin.register(BillingTransaction)
class BillingTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "transaction_type",
        "corporate_name",
        "amount",
        "currency",
        "state",
        "provider",
        "created_at",
    ]
    list_filter = ["state", "transaction_type__category", "provider", "currency"]
    search_fields = [
        "reference",
        "corporate_name",
        "user_email",
        "provider_reference",
        "message",
    ]
    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
        "source_ip",
        "user_agent",
    ]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Transaction Info", {
            "fields": ("reference", "transaction_type", "state", "message")
        }),
        ("Corporate/User Context", {
            "fields": ("corporate_id", "corporate_name", "user_id", "user_email")
        }),
        ("Related Entities", {
            "fields": ("payment_id", "invoice_id", "subscription_id")
        }),
        ("Amount", {
            "fields": ("amount", "currency")
        }),
        ("Provider", {
            "fields": ("provider", "provider_reference")
        }),
        ("Response", {
            "fields": ("response_code", "response_message", "webhook_response")
        }),
        ("Request Context", {
            "fields": ("source_ip", "user_agent")
        }),
        ("Metadata", {
            "fields": ("metadata",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "action_type",
        "entity_type",
        "entity_id",
        "user_email",
        "corporate_id",
        "created_at",
    ]
    list_filter = ["action_type", "entity_type"]
    search_fields = [
        "entity_id",
        "user_email",
        "action_description",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "source_ip",
        "user_agent",
    ]
    date_hierarchy = "created_at"
    
    fieldsets = (
        ("Action Info", {
            "fields": ("action_type", "entity_type", "entity_id", "action_description")
        }),
        ("User Context", {
            "fields": ("user_id", "user_email", "corporate_id")
        }),
        ("Changes", {
            "fields": ("old_values", "new_values")
        }),
        ("Request Context", {
            "fields": ("source_ip", "user_agent")
        }),
        ("Metadata", {
            "fields": ("metadata",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


admin.site.register(PlanFeature)
admin.site.register(PlanModule)
admin.site.register(PlanModuleAssignment)
admin.site.register(SubscriptionHistory)
admin.site.register(Promotion)
admin.site.register(PromotionUsage)
admin.site.register(InvoiceLineItem)
admin.site.register(PaymentMethod)
