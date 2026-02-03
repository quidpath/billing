"""
API views for billing service - SECURE: All endpoints require corporate_id for company tracing
"""

import json
import os
import uuid

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Invoice, Payment, PaymentVerification, Plan
from .services import (InvoiceService, PaymentService, PromotionService,
                       SubscriptionService, TrialService, VerificationService)


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
def list_plans(request):
    """List all available plans - PUBLIC: No corporate_id required"""
    try:
        plans = Plan.objects.filter(is_active=True).order_by("price_monthly")
        plans_data = [
            {
                "id": str(p.id),
                "name": p.name,
                "tier": p.tier,
                "description": p.description,
                "price_monthly": float(p.price_monthly),
                "price_quarterly": (
                    float(p.price_quarterly) if p.price_quarterly else None
                ),
                "price_yearly": float(p.price_yearly) if p.price_yearly else None,
                "included_users": p.included_users,
                "additional_user_price": float(p.additional_user_price),
                "max_users": p.max_users,
                "limits": p.limits,
            }
            for p in plans
        ]
        return JsonResponse(
            {"success": True, "data": {"plans": plans_data}}, status=200
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def create_trial(request):
    """Create 30-day free trial - SECURE: Requires corporate_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        trial = TrialService.create_trial_for_corporate(
            corporate_id=str(corporate_id),
            corporate_name=data.get("corporate_name", ""),
            plan_tier=data.get("plan_tier", "starter"),
        )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "trial_id": str(trial.id),
                    "corporate_id": str(trial.corporate_id),  # Return for verification
                    "status": trial.status,
                    "days_remaining": trial.days_remaining(),
                    "end_date": trial.end_date.isoformat(),
                },
            },
            status=201,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def get_trial_status(request):
    """Get trial status - SECURE: Requires corporate_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        trial_status = TrialService.check_trial_status(str(corporate_id))
        # Add corporate_id to response for verification
        if trial_status.get("trial"):
            trial_status["trial"]["corporate_id"] = str(corporate_id)

        return JsonResponse({"success": True, "data": trial_status}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def create_subscription(request):
    """Create subscription - SECURE: Requires corporate_id, traces to company"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")
        corporate_name = data.get("corporate_name", "")
        plan_tier = data.get("plan_tier")
        billing_cycle = data.get("billing_cycle", "monthly")
        additional_users = data.get("additional_users", 0)
        promotion_code = data.get("promotion_code")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        if not plan_tier:
            return JsonResponse(
                {"success": False, "message": "Plan tier is required"}, status=400
            )

        subscription = SubscriptionService.create_subscription(
            corporate_id=str(corporate_id),
            corporate_name=corporate_name,
            plan_tier=plan_tier,
            billing_cycle=billing_cycle,
            additional_users=additional_users,
            promotion_code=promotion_code,
        )

        # Create invoice
        invoice = InvoiceService.create_invoice_for_subscription(subscription)

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "subscription_id": str(subscription.id),
                    "corporate_id": str(
                        subscription.corporate_id
                    ),  # Return for verification
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "total_amount": float(subscription.total_amount),
                    "currency": subscription.currency,
                },
            },
            status=201,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def get_subscription_status(request):
    """Get subscription status - SECURE: Requires corporate_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        subscription = SubscriptionService.get_active_subscription(str(corporate_id))
        if not subscription:
            return JsonResponse(
                {"success": True, "data": {"subscription": None}}, status=200
            )

        # SECURITY: Verify subscription belongs to requested corporate
        if str(subscription.corporate_id) != str(corporate_id):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized: Subscription does not belong to this company",
                },
                status=403,
            )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "subscription": {
                        "id": str(subscription.id),
                        "corporate_id": str(
                            subscription.corporate_id
                        ),  # Return for verification
                        "plan_name": subscription.plan.name,
                        "plan_tier": subscription.plan.tier,
                        "status": subscription.status,
                        "billing_cycle": subscription.billing_cycle,
                        "total_amount": float(subscription.total_amount),
                        "currency": subscription.currency,
                        "end_date": subscription.end_date.isoformat(),
                        "next_billing_date": (
                            subscription.next_billing_date.isoformat()
                            if subscription.next_billing_date
                            else None
                        ),
                    }
                },
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def validate_promotion(request):
    """Validate promotion code - PUBLIC: No corporate_id required for validation"""
    try:
        data = json.loads(request.body) if request.body else {}
        promotion_code = data.get("promotion_code")
        amount = float(data.get("amount", 0))
        plan_tier = data.get("plan_tier", "starter")

        if not promotion_code:
            return JsonResponse(
                {"success": False, "message": "Promotion code required"}, status=400
            )

        from decimal import Decimal

        result = PromotionService.apply_promotion(
            promotion_code=promotion_code,
            corporate_id="",  # Not needed for validation
            amount=Decimal(str(amount)),
            plan_tier=plan_tier,
        )

        if result["success"]:
            return JsonResponse(
                {
                    "success": True,
                    "data": {
                        "valid": True,
                        "discount_amount": float(result["discount_amount"]),
                        "promotion_name": result["promotion"].name,
                    },
                },
                status=200,
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "data": {"valid": False},
                    "message": result["message"],
                },
                status=400,
            )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def list_invoices(request):
    """List invoices - SECURE: Requires corporate_id, only returns company's invoices"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        invoices = InvoiceService.get_corporate_invoices(str(corporate_id))

        # SECURITY: Verify all invoices belong to the requested corporate
        invoices_data = []
        for inv in invoices:
            if str(inv.corporate_id) == str(corporate_id):
                invoices_data.append(
                    {
                        "id": str(inv.id),
                        "corporate_id": str(
                            inv.corporate_id
                        ),  # Include for verification
                        "invoice_number": inv.invoice_number,
                        "status": inv.status,
                        "total_amount": float(inv.total_amount),
                        "currency": inv.currency,
                        "due_date": inv.due_date.isoformat(),
                        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                        "billing_period_start": inv.billing_period_start.isoformat(),
                        "billing_period_end": inv.billing_period_end.isoformat(),
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "invoices": invoices_data,
                    "corporate_id": str(corporate_id),  # Return for verification
                },
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def initiate_payment(request):
    """Initiate payment - SECURE: Verifies invoice belongs to company"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        data = json.loads(request.body) if request.body else {}
        invoice_id = data.get("invoice_id")
        invoice_number = data.get("invoice_number")
        payment_method = data.get("payment_method")
        customer_email = data.get("customer_email")
        customer_phone = data.get("customer_phone")
        corporate_id = data.get("corporate_id")  # Required for security

        # Log incoming request for debugging
        logger.info(
            f"Payment initiation request: invoice_id={invoice_id}, invoice_number={invoice_number}, payment_method={payment_method}, customer_email={customer_email}, customer_phone={customer_phone}, corporate_id={corporate_id}"
        )

        if not invoice_id and not invoice_number:
            logger.warning(
                f"Payment initiation failed: Missing invoice_id and invoice_number"
            )
            return JsonResponse(
                {"success": False, "message": "Invoice ID or invoice number required"},
                status=400,
            )

        if not payment_method or not customer_email:
            logger.warning(
                f"Payment initiation failed: payment_method={payment_method}, customer_email={customer_email}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Payment method and customer email required",
                },
                status=400,
            )

        # Require phone number for M-Pesa payments
        if payment_method == "mpesa" and not customer_phone:
            logger.warning(
                f"Payment initiation failed: M-Pesa payment requires phone number"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Phone number is required for M-Pesa payments",
                },
                status=400,
            )

        # SECURITY: Require corporate_id for payment verification
        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            logger.warning(
                f"Payment initiation failed: Invalid corporate_id={corporate_id}, error={error_msg}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": error_msg
                    or "Corporate ID is required for payment security",
                },
                status=400,
            )

        if invoice_number:
            invoice = Invoice.objects.filter(invoice_number=invoice_number).first()
        else:
            invoice = Invoice.objects.filter(id=invoice_id).first()

        if not invoice:
            logger.warning(
                f"Payment initiation failed: Invoice not found - invoice_id={invoice_id}, invoice_number={invoice_number}"
            )
            return JsonResponse(
                {"success": False, "message": "Invoice not found"}, status=404
            )

        # SECURITY: Verify invoice belongs to the requesting company
        if str(invoice.corporate_id) != str(corporate_id):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized: Invoice does not belong to this company",
                },
                status=403,
            )

        if invoice.status == "paid":
            return JsonResponse(
                {"success": False, "message": "Invoice already paid"}, status=400
            )

        # Set up provider config based on payment method
        provider_config = None
        if payment_method == "mpesa":
            # For sandbox, use a publicly accessible test webhook URL
            # For production, use the actual callback URL
            test_mode = os.environ.get("MPESA_TEST_MODE", "true").lower() == "true"
            if test_mode:
                # Use webhook.site for sandbox testing (publicly accessible test endpoint)
                # You can view webhooks at: https://webhook.site (get your unique URL)
                # For now, using a generic test URL that M-Pesa accepts
                callback_url = os.environ.get(
                    "MPESA_CALLBACK_URL", "https://webhook.site/unique-id-here"
                )
            else:
                # Production requires a real publicly accessible URL
                callback_url = os.environ.get(
                    "MPESA_CALLBACK_URL",
                    f"{request.scheme}://{request.get_host()}/api/billing/payments/webhook/mpesa/",
                )

            logger.info(f"M-Pesa callback URL: {callback_url} (test_mode={test_mode})")

            provider_config = {
                "consumer_key": os.environ.get("MPESA_CONSUMER_KEY", ""),
                "consumer_secret": os.environ.get("MPESA_CONSUMER_SECRET", ""),
                "business_short_code": os.environ.get("MPESA_SHORTCODE", "174379"),
                "passkey": os.environ.get("MPESA_PASSKEY", ""),
                "test_mode": test_mode,
                "callback_url": callback_url,
            }
            # Validate M-Pesa configuration
            if not all(
                [
                    provider_config["consumer_key"],
                    provider_config["consumer_secret"],
                    provider_config["passkey"],
                ]
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "M-Pesa payment gateway is not properly configured. Please contact support.",
                    },
                    status=500,
                )
        elif payment_method in ["card", "bank_transfer"]:
            provider_config = {
                "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "true").lower()
                == "true",
                "callback_url": os.environ.get(
                    "PAYSTACK_CALLBACK_URL",
                    f"{request.scheme}://{request.get_host()}/api/billing/payments/webhook/",
                ),
                "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
            }
            # Validate Paystack configuration
            if not all([provider_config["public_key"], provider_config["secret_key"]]):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Card payment gateway is not properly configured. Please contact support.",
                    },
                    status=500,
                )
        else:
            provider_config = {
                "api_key": os.environ.get("PESAWAY_API_KEY", ""),
                "secret_key": os.environ.get("PESAWAY_SECRET_KEY", ""),
                "merchant_id": os.environ.get("PESAWAY_MERCHANT_ID", ""),
                "test_mode": os.environ.get("PESAWAY_TEST_MODE", "true").lower()
                == "true",
                "callback_url": os.environ.get("PESAWAY_WEBHOOK_URL", ""),
                "webhook_secret": os.environ.get("PESAWAY_WEBHOOK_SECRET", ""),
            }

        # Log payment initiation
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.info(
            f"Initiating payment: method={payment_method}, invoice={invoice.invoice_number}, amount={invoice.total_amount}, phone={customer_phone}"
        )

        try:
            result = PaymentService.initiate_payment(
                invoice=invoice,
                payment_method=payment_method,
                customer_email=customer_email,
                customer_phone=customer_phone,
                provider_config=provider_config,
            )

            # Log result
            logger.info(
                f"Payment initiation result: success={result.get('success')}, message={result.get('message')}"
            )

            # Ensure payment_id is at top level for frontend
            if result.get("success"):
                # Payment service returns payment_id, ensure it's accessible
                if "payment_id" not in result:
                    result["payment_id"] = result.get("data", {}).get("payment_id")
                # Also keep it in data for consistency
                result["data"] = result.get("data", {})
                result["data"]["corporate_id"] = str(corporate_id)
                result["data"]["invoice_corporate_id"] = str(invoice.corporate_id)
                if "payment_id" in result:
                    result["data"]["payment_id"] = result["payment_id"]

            logger.info(
                f"Payment initiation response: success={result.get('success')}, payment_id={result.get('payment_id')}, provider_reference={result.get('provider_reference')}"
            )

            return JsonResponse(result, status=200 if result["success"] else 400)
        except Exception as payment_error:
            # Log the full error with traceback
            error_traceback = traceback.format_exc()
            logger.error(
                f"Error initiating payment: {str(payment_error)}\n{error_traceback}"
            )

            # Provide user-friendly error message
            error_message = str(payment_error)
            if (
                "authentication" in error_message.lower()
                or "access token" in error_message.lower()
            ):
                if payment_method == "mpesa":
                    error_message = "M-Pesa authentication failed. Please check your M-Pesa credentials are correct and valid."
                else:
                    error_message = "Payment gateway authentication failed. Please check your credentials."
            elif "400" in error_message or "bad request" in error_message.lower():
                if payment_method == "mpesa":
                    error_message = "M-Pesa API returned an error. Please verify your M-Pesa credentials (Consumer Key, Consumer Secret, and Passkey) are correct."
                else:
                    error_message = "Payment gateway returned an error. Please check your payment gateway configuration."

            return JsonResponse(
                {"success": False, "message": error_message}, status=500
            )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in payment request: {str(e)}")
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request format. Please check your request data.",
            },
            status=400,
        )
    except Exception as e:
        # Log the full error with traceback
        import traceback

        error_traceback = traceback.format_exc()
        logger.error(
            f"Unexpected error in initiate_payment: {str(e)}\n{error_traceback}"
        )
        return JsonResponse(
            {"success": False, "message": f"An unexpected error occurred: {str(e)}"},
            status=500,
        )


@csrf_exempt
def payment_webhook(request):
    """Payment webhook - SECURE: Verifies signature, traces payment to company"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        payload = json.loads(request.body) if request.body else {}
        headers = dict(request.headers)

        logger.info(
            f"Webhook received: path={request.path}, payload keys={list(payload.keys())}"
        )

        # Determine provider from URL path or header
        provider = "pesaway"  # Default
        if "mpesa" in request.path.lower():
            provider = "mpesa_daraja"
        elif "paystack" in request.path.lower():
            provider = "paystack"

        logger.info(f"Webhook provider determined: {provider}")

        # Configure based on provider
        if provider == "mpesa_daraja":
            provider_config = {
                "consumer_key": os.environ.get("MPESA_CONSUMER_KEY", ""),
                "consumer_secret": os.environ.get("MPESA_CONSUMER_SECRET", ""),
                "business_short_code": os.environ.get("MPESA_SHORTCODE", "174379"),
                "passkey": os.environ.get("MPESA_PASSKEY", ""),
                "test_mode": os.environ.get("MPESA_TEST_MODE", "true").lower()
                == "true",
            }
        elif provider == "paystack":
            provider_config = {
                "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "true").lower()
                == "true",
            }
        else:
            provider_config = {
                "api_key": os.environ.get("PESAWAY_API_KEY", ""),
                "secret_key": os.environ.get("PESAWAY_SECRET_KEY", ""),
                "webhook_secret": os.environ.get("PESAWAY_WEBHOOK_SECRET", ""),
                "test_mode": os.environ.get("PESAWAY_TEST_MODE", "true").lower()
                == "true",
            }

        logger.info(
            f"Webhook received: path={request.path}, provider={provider}, payload keys={list(payload.keys())}"
        )

        result = PaymentService.handle_payment_webhook(
            payload=payload,
            headers=headers,
            provider=provider,
            provider_config=provider_config,
        )

        logger.info(
            f"Webhook processing result: success={result.get('success')}, payment_id={result.get('payment_id')}, message={result.get('message')}"
        )

        # Add corporate_id to result for tracing
        if result.get("success") and result.get("payment_id"):
            try:
                payment = Payment.objects.get(id=result["payment_id"])
                result["data"] = result.get("data", {})
                result["data"]["corporate_id"] = str(payment.corporate_id)
                result["data"]["invoice_corporate_id"] = (
                    str(payment.invoice.corporate_id) if payment.invoice else None
                )
                invoice_status = payment.invoice.status if payment.invoice else "N/A"
                invoice_id = str(payment.invoice.id) if payment.invoice else "N/A"
                logger.info(
                    f"Webhook: Payment {result['payment_id']} updated successfully. Payment Status: {payment.status}, Invoice ID: {invoice_id}, Invoice Status: {invoice_status}"
                )
            except Payment.DoesNotExist:
                logger.warning(
                    f"Webhook: Payment {result.get('payment_id')} not found after webhook processing"
                )
        elif not result.get("success"):
            logger.error(f"Webhook processing failed: {result.get('message')}")

        return JsonResponse(result, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def mpesa_webhook(request):
    """M-Pesa specific webhook endpoint"""
    return payment_webhook(request)


@csrf_exempt
def initiate_verification(request):
    """Initiate payment verification with KES 1 - SECURE: Requires corporate_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")
        corporate_name = data.get("corporate_name", "")
        phone_number = data.get("phone_number")
        email = data.get("email")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        if not phone_number:
            return JsonResponse(
                {"success": False, "message": "Phone number is required"}, status=400
            )

        if not email:
            return JsonResponse(
                {"success": False, "message": "Email is required"}, status=400
            )

        result = VerificationService.initiate_verification(
            corporate_id=str(corporate_id),
            corporate_name=corporate_name,
            phone_number=phone_number,
            email=email,
        )

        return JsonResponse(result, status=200 if result["success"] else 400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def verification_status(request):
    """Get verification status - SECURE: Requires verification_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        verification_id = data.get("verification_id")

        if not verification_id:
            return JsonResponse(
                {"success": False, "message": "Verification ID is required"}, status=400
            )

        result = VerificationService.get_verification_status(str(verification_id))

        return JsonResponse(result, status=200 if result["success"] else 400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def complete_verification(request):
    """Create trial after verification - SECURE: Requires verification_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        verification_id = data.get("verification_id")
        plan_tier = data.get("plan_tier", "starter")

        if not verification_id:
            return JsonResponse(
                {"success": False, "message": "Verification ID is required"}, status=400
            )

        result = VerificationService.create_trial_after_verification(
            verification_id=str(verification_id), plan_tier=plan_tier
        )

        return JsonResponse(result, status=200 if result["success"] else 400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def check_access(request):
    """
    Check if a corporate has active subscription/trial - CRITICAL for access control
    This endpoint is used by the main backend to verify if a company can use Quidpath
    """
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse(
                {
                    "success": False,
                    "has_access": False,
                    "message": error_msg,
                    "reason": "invalid_corporate_id",
                },
                status=400,
            )

        # Check for active trial
        trial_status = TrialService.check_trial_status(str(corporate_id))
        if trial_status.get("has_active_trial"):
            trial = trial_status.get("trial", {})
            return JsonResponse(
                {
                    "success": True,
                    "has_access": True,
                    "access_type": "trial",
                    "corporate_id": str(corporate_id),
                    "trial": {
                        "status": trial.get("status"),
                        "days_remaining": trial.get("days_remaining"),
                        "end_date": trial.get("end_date"),
                    },
                    "message": f"Trial active with {trial.get('days_remaining', 0)} days remaining",
                },
                status=200,
            )

        # Check for active subscription
        subscription = SubscriptionService.get_active_subscription(str(corporate_id))
        if subscription and subscription.status == "active":
            # Check for unpaid invoices
            unpaid_invoices = InvoiceService.get_unpaid_invoices(str(corporate_id))

            return JsonResponse(
                {
                    "success": True,
                    "has_access": True,
                    "access_type": "subscription",
                    "corporate_id": str(corporate_id),
                    "subscription": {
                        "id": str(subscription.id),
                        "plan_name": subscription.plan.name,
                        "plan_tier": subscription.plan.tier,
                        "status": subscription.status,
                        "end_date": subscription.end_date.isoformat(),
                        "next_billing_date": (
                            subscription.next_billing_date.isoformat()
                            if subscription.next_billing_date
                            else None
                        ),
                    },
                    "unpaid_invoices_count": len(unpaid_invoices),
                    "unpaid_invoices": [
                        {
                            "id": str(inv.id),
                            "invoice_number": inv.invoice_number,
                            "amount": float(inv.total_amount),
                            "due_date": inv.due_date.isoformat(),
                        }
                        for inv in unpaid_invoices[:5]
                    ],  # Return up to 5 most recent
                    "message": "Active subscription found",
                },
                status=200,
            )

        # Check if trial expired
        if trial_status.get("trial"):
            trial = trial_status.get("trial", {})
            if trial.get("status") == "expired":
                return JsonResponse(
                    {
                        "success": True,
                        "has_access": False,
                        "access_type": None,
                        "corporate_id": str(corporate_id),
                        "reason": "trial_expired",
                        "message": "Trial period has expired. Please subscribe to continue using Quidpath.",
                        "trial": {
                            "status": "expired",
                            "end_date": trial.get("end_date"),
                        },
                    },
                    status=200,
                )

        # No active trial or subscription
        return JsonResponse(
            {
                "success": True,
                "has_access": False,
                "access_type": None,
                "corporate_id": str(corporate_id),
                "reason": "no_active_subscription",
                "message": "No active subscription or trial found. Please subscribe to use Quidpath.",
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "has_access": False,
                "message": str(e),
                "reason": "error",
            },
            status=500,
        )


@csrf_exempt
def check_payment_status(request):
    """Check payment status by querying provider - SECURE: Requires payment_id and corporate_id"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        data = json.loads(request.body) if request.body else {}
        payment_id = data.get("payment_id")
        corporate_id = data.get("corporate_id")

        logger.info(
            f"check_payment_status called: payment_id={payment_id}, corporate_id={corporate_id}"
        )

        if not payment_id:
            logger.warning("check_payment_status: payment_id missing")
            return JsonResponse(
                {"success": False, "message": "Payment ID is required"}, status=400
            )

        # SECURITY: Require corporate_id for payment verification
        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            logger.warning(f"check_payment_status: invalid corporate_id: {error_msg}")
            return JsonResponse(
                {
                    "success": False,
                    "message": error_msg
                    or "Corporate ID is required for payment security",
                },
                status=400,
            )

        # Get payment
        try:
            payment = Payment.objects.get(id=payment_id)
            logger.info(
                f"Payment found: id={payment.id}, status={payment.status}, method={payment.payment_method}, provider_ref={payment.provider_reference}"
            )
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: payment_id={payment_id}")
            return JsonResponse(
                {"success": False, "message": "Payment not found"}, status=404
            )

        # SECURITY: Verify payment belongs to the requesting company
        if str(payment.corporate_id) != str(corporate_id):
            logger.warning(
                f"Unauthorized payment access: payment.corporate_id={payment.corporate_id}, request.corporate_id={corporate_id}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Unauthorized: Payment does not belong to this company",
                },
                status=403,
            )

        # If already completed, return status
        if payment.status == "success":
            return JsonResponse(
                {
                    "success": True,
                    "payment": {
                        "id": str(payment.id),
                        "status": payment.status,
                        "invoice_id": (
                            str(payment.invoice.id) if payment.invoice else None
                        ),
                        "invoice_status": (
                            payment.invoice.status if payment.invoice else None
                        ),
                    },
                },
                status=200,
            )

        # If failed or cancelled, return status
        if payment.status in ["failed", "cancelled"]:
            logger.info(f"Payment {payment_id} status: {payment.status}")
            return JsonResponse(
                {
                    "success": True,
                    "payment": {
                        "id": str(payment.id),
                        "status": payment.status,
                        "invoice_id": (
                            str(payment.invoice.id) if payment.invoice else None
                        ),
                        "invoice_status": (
                            payment.invoice.status if payment.invoice else None
                        ),
                        "failure_reason": (
                            payment.metadata.get("failure_reason", "")
                            if hasattr(payment, "metadata")
                            else None
                        ),
                    },
                },
                status=200,
            )

        # Query provider for payment status (only for M-Pesa with provider_reference)
        if payment.payment_method == "mpesa" and payment.provider_reference:
            # Set up M-Pesa adapter
            provider_config = {
                "consumer_key": os.environ.get("MPESA_CONSUMER_KEY", ""),
                "consumer_secret": os.environ.get("MPESA_CONSUMER_SECRET", ""),
                "business_short_code": os.environ.get("MPESA_SHORTCODE", "174379"),
                "passkey": os.environ.get("MPESA_PASSKEY", ""),
                "test_mode": os.environ.get("MPESA_TEST_MODE", "true").lower()
                == "true",
            }

            from .adapters.mpesa_daraja import MpesaDarajaAdapter

            adapter = MpesaDarajaAdapter(provider_config)

            # Query M-Pesa for payment status
            logger.info(
                f"Querying M-Pesa payment status for payment_id={payment_id}, CheckoutRequestID={payment.provider_reference}"
            )
            result = adapter.verify_payment(payment.provider_reference)
            logger.info(
                f"M-Pesa query result for payment {payment_id}: status={result.get('status')}, message={result.get('message')}"
            )

            # Update payment status based on result
            if result.get("status") == "success":
                # Payment successful - update payment and invoice
                payment.mark_as_success(
                    payment.provider_reference, result.get("metadata", {})
                )
                logger.info(
                    f"Payment {payment_id} confirmed as successful via M-Pesa query"
                )

                return JsonResponse(
                    {
                        "success": True,
                        "payment": {
                            "id": str(payment.id),
                            "status": "success",
                            "invoice_id": (
                                str(payment.invoice.id) if payment.invoice else None
                            ),
                            "invoice_status": (
                                payment.invoice.status if payment.invoice else None
                            ),
                        },
                    },
                    status=200,
                )
            elif result.get("status") == "failed":
                # Payment failed
                failure_message = result.get("message", "Payment failed")
                payment.mark_as_failed(failure_message)
                logger.info(
                    f"Payment {payment_id} confirmed as failed via M-Pesa query: {failure_message}"
                )

                return JsonResponse(
                    {
                        "success": True,
                        "payment": {
                            "id": str(payment.id),
                            "status": "failed",
                            "invoice_id": (
                                str(payment.invoice.id) if payment.invoice else None
                            ),
                            "invoice_status": (
                                payment.invoice.status if payment.invoice else None
                            ),
                            "failure_reason": failure_message,
                        },
                    },
                    status=200,
                )
            else:
                # Still pending - log the result for debugging
                logger.info(
                    f"Payment {payment_id} still pending. M-Pesa result: {result}"
                )
                return JsonResponse(
                    {
                        "success": True,
                        "payment": {
                            "id": str(payment.id),
                            "status": payment.status,  # Still processing/pending
                            "invoice_id": (
                                str(payment.invoice.id) if payment.invoice else None
                            ),
                            "invoice_status": (
                                payment.invoice.status if payment.invoice else None
                            ),
                            "pending_message": result.get("message", "Payment pending"),
                        },
                    },
                    status=200,
                )
        else:
            # For other payment methods or no provider_reference, return current status
            return JsonResponse(
                {
                    "success": True,
                    "payment": {
                        "id": str(payment.id),
                        "status": payment.status,
                        "invoice_id": (
                            str(payment.invoice.id) if payment.invoice else None
                        ),
                        "invoice_status": (
                            payment.invoice.status if payment.invoice else None
                        ),
                    },
                },
                status=200,
            )

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        logger.error(f"Error checking payment status: {str(e)}\n{error_traceback}")
        return JsonResponse(
            {"success": False, "message": f"Error checking payment status: {str(e)}"},
            status=500,
        )


@csrf_exempt
def payment_history(request):
    """Get payment history - SECURE: Requires corporate_id"""
    try:
        data = json.loads(request.body) if request.body else {}
        corporate_id = data.get("corporate_id")

        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        # Get payments for this corporate
        payments = (
            Payment.objects.filter(corporate_id=str(corporate_id))
            .select_related("invoice")
            .order_by("-created_at")
        )

        # SECURITY: Verify all payments belong to the requested corporate
        payments_data = []
        for pmt in payments:
            if str(pmt.corporate_id) == str(corporate_id):
                payments_data.append(
                    {
                        "id": str(pmt.id),
                        "amount": float(pmt.amount),
                        "currency": pmt.currency,
                        "payment_method": pmt.payment_method,
                        "status": pmt.status,
                        "provider_reference": pmt.provider_reference,
                        "invoice_id": str(pmt.invoice.id) if pmt.invoice else None,
                        "invoice_number": (
                            pmt.invoice.invoice_number if pmt.invoice else None
                        ),
                        "paid_at": pmt.paid_at.isoformat() if pmt.paid_at else None,
                        "created_at": pmt.created_at.isoformat(),
                        "failure_reason": (
                            pmt.failure_reason
                            if hasattr(pmt, "failure_reason")
                            else None
                        ),
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "payments": payments_data,
                    "corporate_id": str(corporate_id),
                },
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def admin_corporate_summary(request, corporate_id):
    """
    Admin endpoint to get comprehensive billing summary for a corporate
    Used by Django admin panel to display billing information
    """
    try:
        # Validate corporate_id
        is_valid, error_msg = validate_corporate_id(corporate_id)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        # Get trial information
        trial_data = None
        trial_status = TrialService.check_trial_status(str(corporate_id))
        if trial_status.get("trial"):
            trial = trial_status["trial"]
            trial_data = {
                "status": trial.get("status"),
                "days_remaining": trial.get("days_remaining"),
                "end_date": trial.get("end_date"),
            }

        # Get subscription information
        subscription_data = None
        subscription = SubscriptionService.get_active_subscription(str(corporate_id))
        if subscription:
            subscription_data = {
                "id": str(subscription.id),
                "plan_name": subscription.plan.name,
                "plan_tier": subscription.plan.tier,
                "status": subscription.status,
                "billing_cycle": subscription.billing_cycle,
                "total_amount": float(subscription.total_amount),
                "currency": subscription.currency,  # Include currency
                "end_date": subscription.end_date.isoformat(),
                "next_billing_date": (
                    subscription.next_billing_date.isoformat()
                    if subscription.next_billing_date
                    else None
                ),
            }

        # Get invoices
        invoices = InvoiceService.get_corporate_invoices(str(corporate_id))
        invoices_data = [
            {
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "status": inv.status,
                "total_amount": float(inv.total_amount),
                "currency": inv.currency,
                "due_date": inv.due_date.isoformat(),
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            }
            for inv in invoices[:10]
        ]  # Return last 10 invoices

        # Get payments
        payments = Payment.objects.filter(corporate_id=str(corporate_id)).order_by(
            "-created_at"
        )[
            :10
        ]  # Last 10 payments

        payments_data = [
            {
                "id": str(pmt.id),
                "amount": float(pmt.amount),
                "payment_method": pmt.payment_method,
                "status": pmt.status,
                "paid_at": pmt.paid_at.isoformat() if pmt.paid_at else None,
                "created_at": pmt.created_at.isoformat(),
            }
            for pmt in payments
        ]

        # Calculate totals
        from decimal import Decimal

        total_invoiced = sum(Decimal(str(inv.total_amount)) for inv in invoices)
        total_paid = sum(
            Decimal(str(inv.total_amount)) for inv in invoices if inv.status == "paid"
        )
        total_outstanding = total_invoiced - total_paid

        totals = {
            "invoiced": float(total_invoiced),
            "paid": float(total_paid),
            "outstanding": float(total_outstanding),
        }

        return JsonResponse(
            {
                "success": True,
                "data": {
                    "corporate_id": str(corporate_id),
                    "trial": trial_data,
                    "subscription": subscription_data,
                    "invoices": invoices_data,
                    "payments": payments_data,
                    "totals": totals,
                },
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": f"Error retrieving billing summary: {str(e)}",
            },
            status=500,
        )


@csrf_exempt
def mpesa_webhook(request):
    """
    M-Pesa STK Push callback webhook handler
    Processes payment status updates from M-Pesa
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Parse webhook data
        if not request.body:
            logger.warning("M-Pesa webhook received with empty body")
            return JsonResponse(
                {"success": False, "message": "Empty request body"}, status=400
            )

        webhook_data = json.loads(request.body)
        logger.info(f"M-Pesa webhook received: {json.dumps(webhook_data, indent=2)}")

        # M-Pesa webhook structure: {"Body": {"stkCallback": {...}}}
        body = webhook_data.get("Body", {})
        stk_callback = body.get("stkCallback", {})

        if not stk_callback:
            logger.warning("M-Pesa webhook missing stkCallback")
            return JsonResponse(
                {"success": False, "message": "Missing stkCallback"}, status=400
            )

        # Extract callback data
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        merchant_request_id = stk_callback.get("MerchantRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc", "")
        callback_metadata = stk_callback.get("CallbackMetadata", {})

        if not checkout_request_id:
            logger.warning("M-Pesa webhook missing CheckoutRequestID")
            return JsonResponse(
                {"success": False, "message": "Missing CheckoutRequestID"}, status=400
            )

        # Find payment by CheckoutRequestID (stored in provider_reference)
        try:
            payment = Payment.objects.get(provider_reference=checkout_request_id)
        except Payment.DoesNotExist:
            logger.warning(
                f"M-Pesa webhook: Payment not found for CheckoutRequestID: {checkout_request_id}"
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Payment not found for CheckoutRequestID: {checkout_request_id}",
                },
                status=404,
            )

        logger.info(
            f"Processing M-Pesa webhook for payment {payment.id}, ResultCode: {result_code}"
        )

        # Process based on ResultCode
        # ResultCode 0 = Success
        # Other codes = Failure (see M-Pesa documentation)
        if result_code == 0:
            # Payment successful
            # Extract receipt number and other metadata
            items = callback_metadata.get("Item", [])
            receipt_number = None
            amount = None
            transaction_date = None
            phone_number = None

            for item in items:
                name = item.get("Name", "")
                value = item.get("Value")

                if name == "MpesaReceiptNumber":
                    receipt_number = str(value) if value else None
                elif name == "Amount":
                    amount = float(value) if value else None
                elif name == "TransactionDate":
                    transaction_date = str(value) if value else None
                elif name == "PhoneNumber":
                    phone_number = str(value) if value else None

            # Prepare metadata
            metadata = {
                "receipt_number": receipt_number,
                "merchant_request_id": merchant_request_id,
                "checkout_request_id": checkout_request_id,
                "result_code": result_code,
                "result_desc": result_desc,
                "amount": amount,
                "transaction_date": transaction_date,
                "phone_number": phone_number,
                "full_callback": stk_callback,
            }

            # Mark payment as successful
            payment.mark_as_success(
                provider_reference=receipt_number or checkout_request_id,
                metadata=metadata,
            )

            logger.info(
                f"Payment {payment.id} marked as successful via webhook. Receipt: {receipt_number}"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment processed successfully",
                    "payment_id": str(payment.id),
                    "receipt_number": receipt_number,
                },
                status=200,
            )
        else:
            # Payment failed
            failure_reason = result_desc or f"M-Pesa ResultCode: {result_code}"

            payment.mark_as_failed(failure_reason)
            payment.provider_metadata = {
                **payment.provider_metadata,
                "webhook_result_code": result_code,
                "webhook_result_desc": result_desc,
                "merchant_request_id": merchant_request_id,
                "checkout_request_id": checkout_request_id,
            }
            payment.save()

            logger.warning(
                f"Payment {payment.id} marked as failed via webhook. ResultCode: {result_code}, Reason: {failure_reason}"
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Payment failure processed",
                    "payment_id": str(payment.id),
                    "result_code": result_code,
                    "failure_reason": failure_reason,
                },
                status=200,
            )

    except json.JSONDecodeError as e:
        logger.error(f"M-Pesa webhook JSON decode error: {str(e)}")
        return JsonResponse(
            {"success": False, "message": f"Invalid JSON: {str(e)}"}, status=400
        )
    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        logger.error(f"Error processing M-Pesa webhook: {str(e)}\n{error_traceback}")
        return JsonResponse(
            {"success": False, "message": f"Error processing webhook: {str(e)}"},
            status=500,
        )
