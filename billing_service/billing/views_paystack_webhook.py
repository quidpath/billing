"""
Paystack Webhook Handler
Handles all Paystack webhook events including corporate registration payments
"""
import json
import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services.paystack_service import PaystackService
from .services.payment_service import PaymentService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """
    Handle Paystack webhook events
    Events: charge.success, charge.failed, transfer.success, etc.
    
    Accepts webhooks from:
    1. Paystack directly (with signature verification)
    2. quidpath-backend proxy (with X-Service-Key authentication)
    """
    try:
        # Get raw body for signature verification
        payload = request.body
        signature = request.headers.get('x-paystack-signature') or request.headers.get('X-Paystack-Signature')
        service_key = request.headers.get('X-Service-Key')
        
        # Check if this is a service-to-service call from quidpath-backend
        from django.conf import settings
        expected_service_key = getattr(settings, 'SERVICE_SECRET', '')
        is_service_call = service_key and expected_service_key and service_key == expected_service_key
        
        if is_service_call:
            logger.info("Webhook authenticated via X-Service-Key (from quidpath-backend)")
        elif signature:
            # Verify Paystack signature
            paystack = PaystackService()
            if not paystack.verify_webhook_signature(payload, signature):
                logger.error("Invalid Paystack webhook signature")
                logger.error(f"Signature received: {signature[:20]}...")
                logger.error(f"Payload length: {len(payload)}")
                return JsonResponse({"error": "Invalid signature"}, status=401)
            logger.info("Webhook authenticated via Paystack signature")
        else:
            logger.warning("Paystack webhook received without signature or service key")
            return JsonResponse({"error": "No authentication provided"}, status=400)
        
        # Parse payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in Paystack webhook")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        event_type = data.get("event")
        event_data = data.get("data", {})
        
        logger.info(f"Paystack webhook received: {event_type}")
        
        # Handle different event types
        if event_type == "charge.success":
            return handle_charge_success(event_data)
        
        elif event_type == "charge.failed":
            return handle_charge_failed(event_data)
        
        elif event_type == "transfer.success":
            return handle_transfer_success(event_data)
        
        elif event_type == "transfer.failed":
            return handle_transfer_failed(event_data)
        
        else:
            logger.info(f"Unhandled Paystack event type: {event_type}")
            return HttpResponse(status=200)  # Acknowledge receipt
    
    except Exception as e:
        logger.error(f"Error processing Paystack webhook: {e}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)


def handle_charge_success(data):
    """
    Handle successful charge event
    This is called when payment is successful
    """
    try:
        reference = data.get("reference")
        amount = data.get("amount", 0) / 100  # Convert from kobo to main unit
        currency = data.get("currency", "KES")
        customer = data.get("customer", {})
        metadata = data.get("metadata", {})
        authorization = data.get("authorization", {})
        
        logger.info(f"Charge success: {reference}, amount: {amount} {currency}, metadata: {metadata}")
        
        # Check if this is a corporate registration payment
        registration_type = metadata.get("type") or metadata.get("registration_type")
        
        if registration_type == "corporate_registration":
            logger.info(f"Handling as corporate registration payment: {reference}")
            return handle_corporate_registration_payment(data)
        
        # Check if this is a subscription payment
        elif metadata.get("subscription_id") or metadata.get("invoice_id"):
            logger.info(f"Handling as subscription payment: {reference}")
            return handle_subscription_payment(data)
        
        # Generic payment handling
        else:
            logger.info(f"Generic payment success: {reference}")
            # Update payment record if exists
            try:
                from .models.payment import Payment
                payment = Payment.objects.filter(provider_reference=reference).first()
                if payment:
                    logger.info(f"Found payment {payment.id} for reference {reference}")
                    payment.mark_as_success(reference, data)
                    logger.info(f"Payment {payment.id} marked as success")
                else:
                    logger.warning(f"No payment record found for reference {reference}")
            except Exception as e:
                logger.error(f"Could not update payment record: {e}", exc_info=True)
            
            return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling charge success: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


def handle_charge_failed(data):
    """
    Handle failed charge event
    """
    try:
        reference = data.get("reference")
        logger.warning(f"Charge failed: {reference}")
        
        # Update payment record
        try:
            from .models.payment import Payment
            payment = Payment.objects.filter(provider_reference=reference).first()
            if payment:
                payment.mark_as_failed(data.get("gateway_response", "Payment failed"))
                logger.info(f"Payment {payment.id} marked as failed")
        except Exception as e:
            logger.warning(f"Could not update payment record: {e}")
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling charge failed: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


def handle_corporate_registration_payment(data):
    """
    Handle corporate registration payment success
    Triggers corporate creation in main backend
    """
    try:
        reference = data.get("reference")
        metadata = data.get("metadata", {})
        registration_id = metadata.get("registration_id")
        
        logger.info(f"Corporate registration payment success: {reference}, reg_id: {registration_id}")
        
        if not registration_id:
            logger.error("No registration_id in metadata")
            return HttpResponse(status=200)
        
        # Call main backend to create corporate
        import requests
        import os
        
        backend_url = os.environ.get("BACKEND_URL", "https://stage-api.quidpath.com")
        verify_url = f"{backend_url}/corporate/payment/verify"
        
        response = requests.post(
            verify_url,
            json={
                "registration_id": registration_id,
                "reference": reference
            },
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Corporate created successfully for registration {registration_id}")
        else:
            logger.error(f"Failed to create corporate: {response.status_code}, {response.text}")
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling corporate registration payment: {e}", exc_info=True)
        return HttpResponse(status=200)  # Still acknowledge to Paystack


def handle_subscription_payment(data):
    """
    Handle subscription payment success
    Updates payment record, marks invoice as paid, and activates subscription
    """
    try:
        reference = data.get("reference")
        metadata = data.get("metadata", {})
        
        logger.info(f"Subscription payment success: {reference}, metadata: {metadata}")
        logger.info(f"Full webhook data: {json.dumps(data, indent=2)}")
        
        # Find payment by provider reference
        from .models.payment import Payment
        payment = Payment.objects.filter(provider_reference=reference).first()
        
        # If not found by provider_reference, try to find by metadata
        if not payment and metadata.get("payment_id"):
            logger.info(f"Payment not found by reference, trying payment_id: {metadata.get('payment_id')}")
            try:
                payment = Payment.objects.get(id=metadata.get("payment_id"))
                logger.info(f"Found payment by payment_id: {payment.id}")
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found by payment_id either")
        
        # If still not found, try to find by invoice_id
        if not payment and metadata.get("invoice_id"):
            logger.info(f"Payment not found, trying invoice_id: {metadata.get('invoice_id')}")
            payment = Payment.objects.filter(
                invoice_id=metadata.get("invoice_id"),
                status__in=["pending", "processing"]
            ).first()
            if payment:
                logger.info(f"Found payment by invoice_id: {payment.id}")
        
        if not payment:
            logger.error(f"Payment not found for reference: {reference}, metadata: {metadata}")
            logger.error(f"Searched by: provider_reference={reference}, payment_id={metadata.get('payment_id')}, invoice_id={metadata.get('invoice_id')}")
            
            # List recent pending payments for debugging
            recent_payments = Payment.objects.filter(
                status__in=["pending", "processing"]
            ).order_by("-created_at")[:5]
            logger.error(f"Recent pending payments: {[str(p.id) for p in recent_payments]}")
            
            return HttpResponse(status=200)
        
        logger.info(f"Found payment {payment.id}, current status: {payment.status}, invoice: {payment.invoice_id}")
        
        # Update provider_reference if it wasn't set
        if not payment.provider_reference:
            logger.info(f"Setting provider_reference to {reference}")
            payment.provider_reference = reference
            payment.save(update_fields=["provider_reference"])
        
        # Mark payment as success (this will also mark invoice as paid)
        payment.mark_as_success(reference, data)
        
        logger.info(f"Payment {payment.id} marked as success")
        
        # Verify invoice was marked as paid
        if payment.invoice:
            payment.invoice.refresh_from_db()
            logger.info(f"Invoice {payment.invoice.id} status after payment: {payment.invoice.status}")
            
            if payment.invoice.status != "paid":
                logger.error(f"Invoice {payment.invoice.id} was not marked as paid! Forcing update...")
                payment.invoice.mark_as_paid(reference, "paystack")
                payment.invoice.refresh_from_db()
                logger.info(f"Invoice {payment.invoice.id} manually marked as paid, new status: {payment.invoice.status}")
        else:
            logger.warning(f"Payment {payment.id} has no associated invoice")
        
        # Verify subscription was activated
        if payment.subscription:
            payment.subscription.refresh_from_db()
            logger.info(f"Subscription {payment.subscription.id} status after payment: {payment.subscription.status}")
            
            if payment.subscription.status != "active":
                logger.error(f"Subscription {payment.subscription.id} was not activated! Forcing update...")
                payment.subscription.status = "active"
                payment.subscription.save(update_fields=["status", "updated_at"])
                payment.subscription.refresh_from_db()
                logger.info(f"Subscription {payment.subscription.id} manually activated, new status: {payment.subscription.status}")
        else:
            logger.warning(f"Payment {payment.id} has no associated subscription")
        
        logger.info(f"Subscription payment fully processed: {reference}")
        logger.info(f"Final status - Payment: {payment.status}, Invoice: {payment.invoice.status if payment.invoice else 'N/A'}, Subscription: {payment.subscription.status if payment.subscription else 'N/A'}")
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling subscription payment: {e}", exc_info=True)
        return HttpResponse(status=200)


def handle_transfer_success(data):
    """
    Handle successful transfer (refund) event
    """
    try:
        reference = data.get("reference")
        logger.info(f"Transfer success: {reference}")
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling transfer success: {e}", exc_info=True)
        return HttpResponse(status=200)


def handle_transfer_failed(data):
    """
    Handle failed transfer event
    """
    try:
        reference = data.get("reference")
        logger.warning(f"Transfer failed: {reference}")
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error handling transfer failed: {e}", exc_info=True)
        return HttpResponse(status=200)
