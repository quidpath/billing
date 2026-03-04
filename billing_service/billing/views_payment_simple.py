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
    Request body: corporate_id, corporate_name, plan_id, phone_number, billing_cycle (optional).
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
            f"Payment initiation: corporate_id={corporate_id}, "
            f"plan={plan.name}, phone={phone_number}"
        )
        
        # Step 1: Create or get subscription
        subscription = SubscriptionService.create_subscription(
            corporate_id=str(corporate_id),
            corporate_name=corporate_name,
            plan_tier=plan.tier,
            billing_cycle=billing_cycle,
            additional_users=0,
            promotion_code=None,
        )
        
        logger.info(f"Subscription created: {subscription.id}")
        
        # Step 2: Create invoice
        invoice = InvoiceService.create_invoice_for_subscription(subscription)
        
        logger.info(f"Invoice created: {invoice.id}, amount: {invoice.total_amount}")
        
        # Step 3: Initiate M-Pesa payment
        mpesa_service = MpesaService()
        
        # Format phone number
        if not phone_number.startswith("254"):
            if phone_number.startswith("0"):
                phone_number = "254" + phone_number[1:]
            elif phone_number.startswith("+254"):
                phone_number = phone_number[1:]
            else:
                phone_number = "254" + phone_number
        
        # Initiate STK push
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=float(invoice.total_amount),
            account_reference=f"SUB-{str(subscription.id)[:8]}",
            transaction_desc=f"{plan.name} Subscription",
            entity_id=str(corporate_id),
        )
        
        if result["success"]:
            # Create payment record
            from .models import Payment
            
            payment = Payment.objects.create(
                payment_type="subscription",
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
                },
            )
            
            logger.info(
                f"Payment initiated successfully: payment_id={payment.id}, "
                f"checkout_request_id={result['checkout_request_id']}"
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
