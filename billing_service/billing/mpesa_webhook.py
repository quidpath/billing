"""
M-Pesa callback handler for unified billing.
Uses get_clean_data and ResponseProvider; method check inside view (no require_http_methods).
"""

import logging
from datetime import datetime

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Invoice, InvoiceLineItem, Payment, Subscription
from .utils.request_response import ResponseProvider, get_clean_data

logger = logging.getLogger(__name__)


@csrf_exempt
def mpesa_callback(request):
    """
    Handle M-Pesa STK Push callback. Safaricom sends POST with JSON body.
    """
    err = ResponseProvider.method_not_allowed(["POST"])
    if request.method != "POST":
        return err

    data, err_response = get_clean_data(
        request, allowed_methods=["POST"], require_json_body=True
    )
    if err_response is not None:
        return err_response

    try:
        logger.info("M-Pesa callback received: %s", data)

        body = data.get("Body", {}) or {}
        stk_callback = body.get("stkCallback", {}) or {}
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        merchant_request_id = stk_callback.get("MerchantRequestID")

        if not checkout_request_id:
            logger.error("No CheckoutRequestID in callback")
            return ResponseProvider.raw({"ResultCode": 1, "ResultDesc": "Invalid callback"})

        from .services import PaymentService

        payment = PaymentService.get_payment_by_checkout_request_id(checkout_request_id)
        if not payment:
            logger.error("Payment not found for CheckoutRequestID: %s", checkout_request_id)
            return ResponseProvider.raw({"ResultCode": 1, "ResultDesc": "Payment not found"})

        if result_code == 0:
            callback_metadata = stk_callback.get("CallbackMetadata", {}) or {}
            items = callback_metadata.get("Item", []) or []

            receipt_number = None
            transaction_date = None
            amount = None
            phone_number = None

            for item in items:
                name = item.get("Name")
                value = item.get("Value")
                if name == "MpesaReceiptNumber":
                    receipt_number = value
                elif name == "TransactionDate":
                    try:
                        transaction_date = datetime.strptime(
                            str(value), "%Y%m%d%H%M%S"
                        )
                    except (ValueError, TypeError):
                        transaction_date = None
                elif name == "Amount":
                    amount = value
                elif name == "PhoneNumber":
                    phone_number = value

            if transaction_date:
                transaction_date = timezone.make_aware(transaction_date)
            else:
                transaction_date = timezone.now()

            payment.status = "success"
            payment.mpesa_receipt_number = receipt_number
            payment.mpesa_transaction_date = transaction_date
            payment.provider_reference = receipt_number
            payment.paid_at = timezone.now()
            if not payment.metadata:
                payment.metadata = {}
            payment.metadata["callback_data"] = data
            payment.save()

            if payment.subscription:
                payment.subscription.status = "active"
                payment.subscription.save()

                invoice = Invoice.objects.create(
                    corporate_id=payment.corporate_id,
                    corporate_name=payment.corporate_name,
                    subscription=payment.subscription,
                    invoice_number=f"INV-{payment.subscription.id.hex[:8].upper()}-{timezone.now().strftime('%Y%m%d')}",
                    status="paid",
                    subtotal=payment.amount,
                    tax_amount=0,
                    total_amount=payment.amount,
                    currency="KES",
                    due_date=timezone.now().date(),
                    paid_at=timezone.now(),
                    payment_provider_reference=receipt_number,
                    payment_provider="mpesa_direct",
                )
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=f"{payment.subscription.plan.name} Subscription - Monthly",
                    quantity=1,
                    unit_price=payment.amount,
                    total_price=payment.amount,
                )
                payment.invoice = invoice
                payment.save()

                logger.info(
                    "Invoice %s created for subscription %s",
                    invoice.invoice_number,
                    payment.subscription.id,
                )
                logger.info("Subscription %s activated", payment.subscription.id)

            logger.info("Payment %s successful. Receipt: %s", payment.id, receipt_number)

        else:
            payment.status = "failed"
            if not payment.metadata:
                payment.metadata = {}
            payment.metadata["failure_reason"] = result_desc
            payment.metadata["callback_data"] = data
            payment.save()
            logger.warning("Payment %s failed: %s", payment.id, result_desc)

        return ResponseProvider.raw({"ResultCode": 0, "ResultDesc": "Success"})

    except Exception as e:
        logger.exception("Error processing M-Pesa callback: %s", e)
        return ResponseProvider.raw({"ResultCode": 1, "ResultDesc": str(e)}, status=500)
