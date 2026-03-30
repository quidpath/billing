"""
Individual User Payment with Multiple Payment Methods
Supports: Card, Mobile Money, Bank Transfer via Paystack
"""
import logging
import os
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services.paystack_service import PaystackService
from .services.subscription_service import SubscriptionService
from .services.invoice_service import InvoiceService
from .services.plan_service import PlanService
from .utils.request_response import get_clean_data, ResponseProvider

logger = logging.getLogger(__name__)


@csrf_exempt
def initiate_individual_payment(request):
    """
    Initiate payment for individual user subscription
    Supports multiple payment methods: card, mobile_money, bank_transfer
    """
    data, err = get_clean_data(request, allowed_methods=["POST"], require_json_body=True)
    if err is not None:
        return err
    
    try:
        d = data or {}
        user_id = d.get("user_id")
        user_email = d.get("email")
        user_name = d.get("name", "")
        plan_id = d.get("plan_id")
        payment_method = d.get("payment_method", "card")  # card, mobile_money, bank_transfer
        phone_number = d.get("phone_number", "")
        billing_cycle = d.get("billing_cycle", "monthly")
        
        # Validate required fields
        if not user_id or not user_email or not plan_id:
            return ResponseProvider.error("user_id, email, and plan_id are required", status=400)
        
        if payment_method == "mobile_money" and not phone_number:
            return ResponseProvider.error("Phone number is required for mobile money", status=400)
        
        # Get plan
        plan = PlanService.get_plan_by_id(plan_id)
        if not plan:
            return ResponseProvider.error("Plan not found", status=404)
        
        logger.info(f"Initiating payment: user={user_email}, plan={plan.name}, method={payment_method}")
        
        # Create subscription
        subscription = SubscriptionService.create_subscription(
            corporate_id=str(user_id),  # Use user_id as corporate_id for individuals
            corporate_name=user_name,
            plan_tier=plan.tier,
            billing_cycle=billing_cycle,
        )
        subscription.subscription_type = "individual"
        subscription.save(update_fields=["subscription_type"])
        
        # Create invoice
        invoice = InvoiceService.create_invoice_for_subscription(subscription)
        
        logger.info(f"Created subscription {subscription.id} and invoice {invoice.id}")
        
        # Initialize Paystack payment
        paystack = PaystackService()
        
        frontend_url = os.environ.get("FRONTEND_URL", "https://stage.quidpath.com")
        callback_url = f"{frontend_url}/payment/verify?subscription_id={subscription.id}&invoice_id={invoice.id}"
        
        # Determine channels based on payment method
        channels = []
        if payment_method == "card":
            channels = ["card"]
        elif payment_method == "mobile_money":
            channels = ["mobile_money"]
        elif payment_method == "bank_transfer":
            channels = ["bank", "bank_transfer"]
        else:
            channels = ["card"]  # Default to card
        
        payment_result = paystack.initialize_transaction(
            amount=invoice.total_amount,
            email=user_email,
            currency=invoice.currency,
            callback_url=callback_url,
            metadata={
                "type": "individual_subscription",
                "user_id": str(user_id),
                "subscription_id": str(subscription.id),
                "invoice_id": str(invoice.id),
                "plan_name": plan.name,
                "payment_method": payment_method,
            },
            channels=channels
        )
        
        if payment_result.get("success"):
            # Create payment record
            from .models.payment import Payment
            
            payment = Payment.objects.create(
                payment_type="individual",
                corporate_id=str(user_id),
                corporate_name=user_name,
                subscription=subscription,
                invoice=invoice,
                amount=invoice.total_amount,
                currency=invoice.currency,
                customer_email=user_email,
                customer_phone=phone_number,
                status="pending",
                payment_method=payment_method,
                provider="paystack",
                provider_reference=payment_result.get("reference"),
                metadata={
                    "plan_id": str(plan.id),
                    "plan_name": plan.name,
                    "payment_method": payment_method,
                }
            )
            
            logger.info(f"Payment initiated: {payment.id}, reference: {payment_result.get('reference')}")
            
            return ResponseProvider.success(
                data={
                    "payment_id": str(payment.id),
                    "subscription_id": str(subscription.id),
                    "invoice_id": str(invoice.id),
                    "payment_reference": payment_result.get("reference"),
                    "authorization_url": payment_result.get("authorization_url"),
                    "access_code": payment_result.get("access_code"),
                    "amount": float(invoice.total_amount),
                    "currency": invoice.currency,
                },
                message="Payment initiated. Please complete payment."
            )
        else:
            logger.error(f"Payment initiation failed: {payment_result.get('message')}")
            return ResponseProvider.error(
                payment_result.get("message", "Payment initiation failed"),
                status=400
            )
    
    except Exception as e:
        logger.exception(f"Error initiating individual payment: {e}")
        return ResponseProvider.error(str(e), status=500)


@csrf_exempt
def verify_individual_payment(request):
    """
    Verify individual payment and activate subscription
    """
    data, err = get_clean_data(request, allowed_methods=["POST"], require_json_body=True)
    if err is not None:
        return err
    
    try:
        d = data or {}
        payment_reference = d.get("reference")
        subscription_id = d.get("subscription_id")
        
        if not payment_reference:
            return ResponseProvider.error("Payment reference is required", status=400)
        
        # Verify with Paystack
        paystack = PaystackService()
        result = paystack.verify_transaction(payment_reference)
        
        if not result.get("success"):
            return ResponseProvider.error(result.get("message", "Verification failed"), status=400)
        
        if result.get("status") != "success":
            return ResponseProvider.error(f"Payment not successful: {result.get('status')}", status=400)
        
        # Update payment record
        from .models.payment import Payment
        
        payment = Payment.objects.filter(provider_reference=payment_reference).first()
        
        if not payment:
            return ResponseProvider.error("Payment record not found", status=404)
        
        # Mark payment as success
        payment.mark_as_success(payment_reference, result)
        
        logger.info(f"Payment verified and marked as success: {payment.id}")
        
        # Get subscription details
        subscription = payment.subscription
        
        return ResponseProvider.success(
            data={
                "payment_id": str(payment.id),
                "subscription_id": str(subscription.id),
                "status": "completed",
                "message": "Payment successful! Your subscription is now active.",
                "subscription": {
                    "plan_name": subscription.plan.name,
                    "status": subscription.status,
                    "end_date": subscription.end_date.isoformat(),
                }
            }
        )
    
    except Exception as e:
        logger.exception(f"Error verifying individual payment: {e}")
        return ResponseProvider.error(str(e), status=500)
