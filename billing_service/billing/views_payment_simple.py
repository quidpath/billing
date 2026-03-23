"""
Simplified payment initiation endpoint that accepts plan_id.
Uses get_clean_data and ResponseProvider; DB via PlanService.
"""

import logging
import uuid

from django.views.decorators.csrf import csrf_exempt

from .services import InvoiceService, PlanService, SubscriptionService
from .services.mpesa_service import MpesaService
from .utils.request_response import ResponseProvider, get_clean_data

logger = logging.getLogger(__name__)


def validate_corporate_id(corporate_id: str) -> tuple[bool, str]:
    """Validate corporate_id format"""
    if not corporate_id:
        return False, "Corporate ID is required"
    try:
        uuid.UUID(str(corporate_id))
        return True, ""
    except ValueError:
        return False, "Invalid corporate ID format"


@csrf_exempt
def initiate_payment_simple(request):
    """
    Simplified payment initiation - accepts plan_id and creates everything automatically.
    Request body: corporate_id, corporate_name, plan_id, phone_number,
                  billing_cycle (optional), subscription_type (individual|organization).
    """
    data, err = get_clean_data(request, allowed_methods=["POST"], require_json_body=True)
    if err is not None:
        return err
    try:
        d = data or {}
        corporate_id = d.get("corporate_id")
        corporate_name = d.get("corporate_name", "")
        plan_id = d.get("plan_id")
        phone_number = d.get("phone_number")
        billing_cycle = d.get("billing_cycle", "monthly")
        subscription_type = d.get("subscription_type", "organization")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return ResponseProvider.error(error_msg, status=400)

        if not plan_id:
            return ResponseProvider.error("Plan ID is required", status=400)

        if not phone_number:
            return ResponseProvider.error("Phone number is required", status=400)

        plan = PlanService.get_plan_by_id(plan_id)
        if not plan:
            return ResponseProvider.error("Plan not found or inactive", status=404)

        logger.info(
            "Payment initiation: corporate_id=%s, plan=%s, phone=%s, type=%s",
            corporate_id, plan.name, phone_number, subscription_type,
        )

        # Idempotency: prevent duplicate STK pushes within 5 minutes
        from django.utils import timezone
        from datetime import timedelta
        from .models import Payment as PaymentModel
        recent_cutoff = timezone.now() - timedelta(minutes=5)
        duplicate = PaymentModel.objects.filter(
            corporate_id=str(corporate_id),
            status="processing",
            metadata__plan_id=str(plan_id),
            created_at__gte=recent_cutoff,
        ).first()
        if duplicate:
            logger.warning(
                "Duplicate payment attempt blocked: corporate_id=%s, plan_id=%s, existing_payment=%s",
                corporate_id, plan_id, duplicate.id,
            )
            return ResponseProvider.success(
                data={
                    "payment_id": str(duplicate.id),
                    "subscription_id": str(duplicate.subscription_id) if duplicate.subscription_id else None,
                    "invoice_id": str(duplicate.invoice_id) if duplicate.invoice_id else None,
                    "checkout_request_id": duplicate.mpesa_checkout_request_id,
                    "amount": float(duplicate.amount),
                    "phone_number": duplicate.customer_phone,
                },
                message="Payment already in progress. Please check your phone for the M-Pesa prompt.",
            )

        # Step 1: Create subscription
        subscription = SubscriptionService.create_subscription(
            corporate_id=str(corporate_id),
            corporate_name=corporate_name,
            plan_tier=plan.tier,
            billing_cycle=billing_cycle,
        )
        # Set subscription type after creation
        subscription.subscription_type = subscription_type
        subscription.save(update_fields=["subscription_type"])

        logger.info("Subscription created: %s", subscription.id)

        # Step 2: Create invoice
        invoice = InvoiceService.create_invoice_for_subscription(subscription)
        logger.info("Invoice created: %s, amount: %s", invoice.id, invoice.total_amount)

        # Step 3: Format phone number
        if not phone_number.startswith("254"):
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+254"):
                phone_number = phone_number[1:]
            else:
                phone_number = "254" + phone_number

        # Step 4: Initiate STK push
        mpesa_service = MpesaService()
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=float(invoice.total_amount),
            account_reference=f"SUB-{str(subscription.id)[:8]}",
            transaction_desc=f"{plan.name} Subscription",
            entity_id=str(corporate_id),
        )

        if result["success"]:
            from .models import Payment

            payment = Payment.objects.create(
                payment_type=subscription_type,
                corporate_id=corporate_id,
                corporate_name=corporate_name,
                subscription=subscription,
                invoice=invoice,
                amount=invoice.total_amount,
                customer_phone=phone_number,
                status="processing",
                payment_method="mpesa",
                provider="mpesa_direct",
                mpesa_checkout_request_id=result["checkout_request_id"],
                mpesa_merchant_request_id=result["merchant_request_id"],
                idempotency_key=result["idempotency_key"],
                metadata={
                    "plan_id": str(plan.id),
                    "plan_name": plan.name,
                    "plan_tier": plan.tier,
                    "subscription_type": subscription_type,
                },
            )

            logger.info(
                "Payment initiated: payment_id=%s, checkout_request_id=%s",
                payment.id, result["checkout_request_id"],
            )

            return ResponseProvider.success(
                data={
                    "payment_id": str(payment.id),
                    "subscription_id": str(subscription.id),
                    "invoice_id": str(invoice.id),
                    "checkout_request_id": result["checkout_request_id"],
                    "merchant_request_id": result["merchant_request_id"],
                    "amount": float(invoice.total_amount),
                    "phone_number": phone_number,
                },
                message="Payment initiated. Please check your phone for M-Pesa prompt.",
            )
        logger.error("M-Pesa STK push failed: %s", result.get("message"))
        return ResponseProvider.error(result.get("message", "STK push failed"), status=400)

    except Exception as e:
        logger.exception("Payment initiation error: %s", e)
        return ResponseProvider.error("Payment initiation failed: %s" % str(e), status=500)
