"""
Payment service for processing payments - Paystack Only
"""

import json
import logging
from decimal import Decimal
from typing import Dict, Optional

from django.utils import timezone

from ..adapters.paystack import PaystackAdapter
from ..models.invoice import Invoice
from ..models.payment import Payment
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for processing payments via Paystack"""

    @staticmethod
    def get_payment_by_id(payment_id):
        """Get payment by id. Raises Payment.DoesNotExist if not found."""
        return Payment.objects.get(id=payment_id)

    @staticmethod
    def get_payment_by_checkout_request_id(checkout_request_id):
        """Get payment by mpesa_checkout_request_id. Returns None if not found."""
        return Payment.objects.filter(
            mpesa_checkout_request_id=checkout_request_id
        ).first()

    @staticmethod
    def get_payment_by_provider_reference(provider_reference):
        """Get payment by provider_reference. Raises Payment.DoesNotExist if not found."""
        return Payment.objects.get(provider_reference=provider_reference)

    @staticmethod
    def get_payments_by_corporate(corporate_id, order_by="-created_at", limit=None):
        """Get payments for corporate. Returns queryset (use list() or slice)."""
        qs = Payment.objects.filter(corporate_id=str(corporate_id)).select_related(
            "invoice"
        ).order_by(order_by)
        if limit is not None:
            return list(qs[:limit])
        return list(qs)

    @staticmethod
    def initiate_payment(
        invoice: Invoice,
        payment_method: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        provider_config: Optional[Dict] = None,
    ) -> Dict:
        """Initiate payment for an invoice via Paystack"""
        import os

        # All payments go through Paystack
        provider = "paystack"
        if not provider_config:
            provider_config = {
                "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "false").lower()
                == "true",
                "callback_url": os.environ.get("PAYSTACK_CALLBACK_URL", ""),
                "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
            }

        adapter = PaystackAdapter(provider_config)

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

        # Initiate payment with Paystack
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
        """Handle payment webhook from Paystack"""
        import os

        # Only Paystack is supported
        if not provider_config:
            provider_config = {
                "public_key": os.environ.get("PAYSTACK_PUBLIC_KEY", ""),
                "secret_key": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "webhook_secret": os.environ.get("PAYSTACK_SECRET_KEY", ""),
                "test_mode": os.environ.get("PAYSTACK_TEST_MODE", "false").lower()
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
            logger.warning(f"Invalid webhook signature from Paystack")
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
