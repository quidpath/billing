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
    """
    try:
        # Get raw body for signature verification
        payload = request.body
        signature = request.headers.get('x-paystack-signature') or request.headers.get('X-Paystack-Signature')
        
        if not signature:
            logger.warning("Paystack webhook received without signature")
            return JsonResponse({"error": "No signature provided"}, status=400)
        
        # Verify signature
        paystack = PaystackService()
        if not paystack.verify_webhook_signature(payload, signature):
            logger.error("Invalid Paystack webhook signature")
            return JsonResponse({"error": "Invalid signature"}, status=401)
        
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
        
        logger.info(f"Charge success: {reference}, amount: {amount} {currency}")
        
        # Check if this is a corporate registration payment
        registration_type = metadata.get("type") or metadata.get("registration_type")
        
        if registration_type == "corporate_registration":
            return handle_corporate_registration_payment(data)
        
        # Check if this is a subscription payment
        elif metadata.get("subscription_id") or metadata.get("invoice_id"):
            return handle_subscription_payment(data)
        
        # Generic payment handling
        else:
            logger.info(f"Generic payment success: {reference}")
            # Update payment record if exists
            try:
                from .models.payment import Payment
                payment = Payment.objects.filter(provider_reference=reference).first()
                if payment:
                    payment.mark_as_success(reference, data)
                    logger.info(f"Payment {payment.id} marked as success")
            except Exception as e:
                logger.warning(f"Could not update payment record: {e}")
            
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
    """
    try:
        reference = data.get("reference")
        metadata = data.get("metadata", {})
        
        logger.info(f"Subscription payment success: {reference}")
        
        # Use existing payment service to handle
        result = PaymentService.handle_payment_webhook(
            payload=data,
            headers={},
            provider="paystack"
        )
        
        if result.get("success"):
            logger.info(f"Subscription payment processed: {reference}")
        else:
            logger.error(f"Failed to process subscription payment: {result.get('message')}")
        
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
