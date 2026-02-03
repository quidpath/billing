"""
Payment service for processing payments
"""

import json
import logging
from decimal import Decimal
from typing import Dict, Optional

from django.utils import timezone

from ..adapters.mpesa_daraja import MpesaDarajaAdapter
from ..adapters.paystack import PaystackAdapter
from ..adapters.pesaway import PesawayAdapter
from ..models.invoice import Invoice
from ..models.payment import Payment
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for processing payments"""

    @staticmethod
    def initiate_payment(
        invoice: Invoice,
        payment_method: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        provider_config: Optional[Dict] = None,
    ) -> Dict:
        """Initiate payment for an invoice"""
        import os

        # Determine provider based on payment method
        if payment_method == "mpesa":
            # Use M-Pesa Daraja API for direct STK Push
            provider = "mpesa_daraja"
            if not provider_config:
                provider_config = {
                    "consumer_key": os.environ.get("MPESA_CONSUMER_KEY", ""),
                    "consumer_secret": os.environ.get("MPESA_CONSUMER_SECRET", ""),
                    "business_short_code": os.environ.get("MPESA_SHORTCODE", "174379"),
                    "passkey": os.environ.get("MPESA_PASSKEY", ""),
                    "test_mode": os.environ.get("MPESA_TEST_MODE", "true").lower()
                    == "true",
                    "callback_url": os.environ.get("MPESA_CALLBACK_URL", ""),
                }
            adapter = MpesaDarajaAdapter(provider_config)
        elif payment_method in ["card", "bank_transfer"]:
            # Use Paystack for card and bank payments
            provider = "paystack"
            if not provider_config:
                provider_config = {
                    "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                    "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                    "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "true").lower()
                    == "true",
                    "callback_url": os.environ.get("PAYSTACK_CALLBACK_URL", ""),
                    "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                }
            adapter = PaystackAdapter(provider_config)
        else:
            # Use Pesaway as fallback for other methods
            provider = "pesaway"
            if not provider_config:
                provider_config = {
                    "api_key": os.environ.get("PESAWAY_API_KEY", ""),
                    "secret_key": os.environ.get("PESAWAY_SECRET_KEY", ""),
                    "merchant_id": os.environ.get("PESAWAY_MERCHANT_ID", ""),
                    "test_mode": os.environ.get("PESAWAY_TEST_MODE", "true").lower()
                    == "true",
                    "callback_url": os.environ.get("PESAWAY_CALLBACK_URL", ""),
                    "webhook_secret": os.environ.get("PESAWAY_WEBHOOK_SECRET", ""),
                }
            adapter = PesawayAdapter(provider_config)

        # Create payment record
        payment = Payment.objects.create(
            corporate_id=invoice.corporate_id,
            corporate_name=invoice.corporate_name,
            invoice=invoice,
            amount=invoice.total_amount,
            currency=invoice.currency,
            payment_method=payment_method,
            provider=provider,
            status="pending",
            customer_email=customer_email,
            customer_phone=customer_phone,
        )

        # Prepare metadata with invoice details
        metadata = {
            "invoice_number": invoice.invoice_number,
            "invoice_id": str(invoice.id),
            "payment_id": str(payment.id),
            "corporate_id": str(invoice.corporate_id),
            "description": f"Payment for invoice {invoice.invoice_number}",
        }

        # Initiate payment with the adapter
        result = adapter.initiate_payment(
            amount=invoice.total_amount,
            currency=invoice.currency,
            payment_method=payment_method,
            customer_email=customer_email,
            customer_phone=customer_phone,
            metadata=metadata,
            callback_url=provider_config.get("callback_url"),
        )

        if result.get("status") == "success":
            payment.provider_reference = result.get("provider_reference") or result.get(
                "merchant_request_id"
            )
            payment.provider_metadata = result.get("metadata", {})
            payment.status = "processing"
            payment.save()

            return {
                "success": True,
                "payment_id": str(payment.id),
                "provider_reference": result.get("provider_reference"),
                "merchant_request_id": result.get("merchant_request_id"),
                "checkout_url": result.get("checkout_url"),
                "message": result.get("message", "Payment initiated successfully"),
            }
        else:
            payment.mark_as_failed(result.get("message", "Payment initiation failed"))
            return {
                "success": False,
                "payment_id": str(payment.id),
                "message": result.get("message", "Payment initiation failed"),
            }

    @staticmethod
    def handle_payment_webhook(
        payload: Dict,
        headers: Dict,
        provider: str = "paystack",
        provider_config: Optional[Dict] = None,
    ) -> Dict:
        """Handle payment webhook from provider"""
        import os

        # Select adapter based on provider
        if provider == "mpesa_daraja" or provider == "mpesa":
            if not provider_config:
                provider_config = {
                    "consumer_key": os.environ.get("MPESA_CONSUMER_KEY", ""),
                    "consumer_secret": os.environ.get("MPESA_CONSUMER_SECRET", ""),
                    "business_short_code": os.environ.get("MPESA_SHORTCODE", "174379"),
                    "passkey": os.environ.get("MPESA_PASSKEY", ""),
                    "test_mode": os.environ.get("MPESA_TEST_MODE", "true").lower()
                    == "true",
                }
            adapter = MpesaDarajaAdapter(provider_config)
        elif provider == "pesaway":
            if not provider_config:
                provider_config = {
                    "api_key": os.environ.get("PESAWAY_API_KEY", ""),
                    "secret_key": os.environ.get("PESAWAY_SECRET_KEY", ""),
                    "webhook_secret": os.environ.get("PESAWAY_WEBHOOK_SECRET", ""),
                    "test_mode": os.environ.get("PESAWAY_TEST_MODE", "true").lower()
                    == "true",
                }
            adapter = PesawayAdapter(provider_config)
        else:  # Default to paystack
            if not provider_config:
                provider_config = {
                    "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                    "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                    "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                    "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "true").lower()
                    == "true",
                }
            adapter = PaystackAdapter(provider_config)

        import json

        payload_bytes = (
            json.dumps(payload).encode("utf-8")
            if isinstance(payload, dict)
            else payload
        )

        if not adapter.verify_webhook_signature(payload_bytes, headers):
            logger.warning(f"Invalid webhook signature from {provider}")
            return {
                "success": False,
                "message": "Invalid webhook signature",
            }

        webhook_data = adapter.handle_webhook(payload, headers)

        provider_reference = webhook_data.get("provider_reference")
        if not provider_reference:
            return {
                "success": False,
                "message": "No provider reference in webhook",
            }

        payment = Payment.objects.filter(provider_reference=provider_reference).first()
        if not payment:
            logger.warning(f"Payment not found for reference {provider_reference}")
            # Try to find by CheckoutRequestID if provider_reference is CheckoutRequestID
            checkout_request_id = webhook_data.get("provider_reference")
            if checkout_request_id:
                payment = Payment.objects.filter(
                    provider_reference=checkout_request_id
                ).first()

            if not payment:
                logger.error(
                    f"Payment not found for reference {provider_reference} or CheckoutRequestID {checkout_request_id}"
                )
                return {
                    "success": False,
                    "message": "Payment not found",
                }

        logger.info(
            f"Webhook: Found payment {payment.id} for reference {provider_reference}, current status: {payment.status}"
        )

        if webhook_data.get("status") == "success":
            logger.info(f"Webhook: Marking payment {payment.id} as successful")
            payment.mark_as_success(
                provider_reference, webhook_data.get("metadata", {})
            )
            logger.info(
                f"Webhook: Payment {payment.id} marked as success. Invoice status: {payment.invoice.status if payment.invoice else 'N/A'}"
            )

            # Check if this is a verification payment
            if payment.invoice and payment.invoice.metadata.get("is_verification"):
                logger.info(f"Verification payment detected: {provider_reference}")
                from .verification_service import VerificationService

                receipt_number = webhook_data.get("metadata", {}).get(
                    "mpesa_receipt", ""
                )
                VerificationService.handle_verification_payment_success(
                    provider_reference, receipt_number, webhook_data.get("metadata", {})
                )

            # Send payment confirmation notification
            try:
                logger.info(
                    f"Payment confirmed for invoice {payment.invoice.invoice_number}"
                )
                # TODO: Fetch corporate email and send notification
                # NotificationService.send_payment_confirmation_notification(payment, corporate_email)
            except Exception as e:
                logger.error(f"Error sending payment notification: {str(e)}")

            return {
                "success": True,
                "payment_id": str(payment.id),
                "message": "Payment confirmed",
            }
        elif webhook_data.get("status") == "failed":
            payment.mark_as_failed(webhook_data.get("message", "Payment failed"))

            # Check if this is a verification payment
            if payment.invoice and payment.invoice.metadata.get("is_verification"):
                logger.info(f"Verification payment failed: {provider_reference}")
                from .verification_service import VerificationService

                VerificationService.handle_verification_payment_failed(
                    provider_reference, webhook_data.get("message", "Payment failed")
                )

            return {
                "success": False,
                "payment_id": str(payment.id),
                "message": "Payment failed",
            }

        return {
            "success": True,
            "payment_id": str(payment.id),
            "message": "Webhook processed",
        }
