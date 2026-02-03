"""
Admin interface for billing models
"""

from django.contrib import admin

from .models import (Invoice, InvoiceLineItem, Payment, PaymentMethod, Plan,
                     PlanFeature, PlanModule, PlanModuleAssignment, Promotion,
                     PromotionUsage, Subscription, SubscriptionHistory, Trial)


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


admin.site.register(PlanFeature)
admin.site.register(PlanModule)
admin.site.register(PlanModuleAssignment)
admin.site.register(SubscriptionHistory)
admin.site.register(Promotion)
admin.site.register(PromotionUsage)
admin.site.register(InvoiceLineItem)
admin.site.register(PaymentMethod)
