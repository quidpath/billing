"""
Admin Fix Endpoints
Endpoints for manually fixing payment/invoice issues
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models.payment import Payment
from .models.invoice import Invoice

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def fix_invoice_status(request):
    """
    Manually fix invoice status based on successful payment
    
    POST /api/billing/admin/fix-invoice/
    Body: {
        "invoice_id": "uuid",
        "payment_reference": "optional_reference"
    }
    
    OR
    
    Body: {
        "payment_id": "uuid"
    }
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        
        invoice_id = data.get("invoice_id")
        payment_id = data.get("payment_id")
        payment_reference = data.get("payment_reference")
        
        if not invoice_id and not payment_id:
            return JsonResponse({
                "success": False,
                "message": "Either invoice_id or payment_id is required"
            }, status=400)
        
        # Find invoice and payment
        invoice = None
        payment = None
        
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                invoice = payment.invoice
                payment_reference = payment.provider_reference or payment_reference
            except Payment.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": f"Payment {payment_id} not found"
                }, status=404)
        
        if invoice_id:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                # Try to find associated payment
                if not payment:
                    payment = Payment.objects.filter(
                        invoice_id=invoice_id,
                        status="success"
                    ).first()
                    if payment:
                        payment_reference = payment.provider_reference or payment_reference
            except Invoice.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": f"Invoice {invoice_id} not found"
                }, status=404)
        
        if not invoice:
            return JsonResponse({
                "success": False,
                "message": "No invoice found"
            }, status=404)
        
        # Check current status
        logger.info(f"Fix request for invoice {invoice.id} ({invoice.invoice_number}), current status: {invoice.status}")
        
        if invoice.status == "paid":
            return JsonResponse({
                "success": True,
                "message": "Invoice is already marked as paid",
                "invoice": {
                    "id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                    "payment_reference": invoice.payment_reference,
                }
            })
        
        # Check if there's a successful payment
        if payment and payment.status == "success":
            logger.info(f"Found successful payment {payment.id}, marking invoice as paid")
            invoice.mark_as_paid(
                payment_reference or payment.provider_reference or "manual_fix",
                payment.provider
            )
            
            return JsonResponse({
                "success": True,
                "message": "Invoice marked as paid successfully",
                "invoice": {
                    "id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                    "payment_reference": invoice.payment_reference,
                },
                "payment": {
                    "id": str(payment.id),
                    "status": payment.status,
                    "amount": float(payment.amount),
                    "provider_reference": payment.provider_reference,
                }
            })
        
        # No successful payment found
        return JsonResponse({
            "success": False,
            "message": "No successful payment found for this invoice",
            "invoice": {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "status": invoice.status,
            },
            "payment": {
                "id": str(payment.id) if payment else None,
                "status": payment.status if payment else None,
            } if payment else None
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error fixing invoice status: {e}", exc_info=True)
        return JsonResponse({
            "success": False,
            "message": f"Error: {str(e)}"
        }, status=500)


@csrf_exempt
@require_POST
def bulk_fix_invoices(request):
    """
    Bulk fix all invoices with successful payments but pending status
    
    POST /api/billing/admin/bulk-fix-invoices/
    Body: {
        "corporate_id": "optional_uuid",
        "dry_run": true/false
    }
    """
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        
        corporate_id = data.get("corporate_id")
        dry_run = data.get("dry_run", True)
        
        # Find all pending invoices with successful payments
        query = Payment.objects.filter(
            status="success",
            invoice__status="pending"
        ).select_related("invoice")
        
        if corporate_id:
            query = query.filter(corporate_id=corporate_id)
        
        payments = list(query)
        
        logger.info(f"Found {len(payments)} invoices to fix (dry_run={dry_run})")
        
        fixed = []
        errors = []
        
        for payment in payments:
            try:
                invoice = payment.invoice
                if not invoice:
                    continue
                
                logger.info(f"Processing invoice {invoice.id} ({invoice.invoice_number})")
                
                if not dry_run:
                    invoice.mark_as_paid(
                        payment.provider_reference or "bulk_fix",
                        payment.provider
                    )
                
                fixed.append({
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "payment_id": str(payment.id),
                    "amount": float(invoice.total_amount),
                    "corporate_id": str(invoice.corporate_id),
                    "corporate_name": invoice.corporate_name,
                })
            except Exception as e:
                logger.error(f"Error fixing invoice {invoice.id}: {e}")
                errors.append({
                    "invoice_id": str(invoice.id),
                    "error": str(e)
                })
        
        return JsonResponse({
            "success": True,
            "dry_run": dry_run,
            "fixed_count": len(fixed),
            "error_count": len(errors),
            "fixed": fixed,
            "errors": errors,
            "message": f"{'Would fix' if dry_run else 'Fixed'} {len(fixed)} invoices"
        })
        
    except Exception as e:
        logger.error(f"Error in bulk fix: {e}", exc_info=True)
        return JsonResponse({
            "success": False,
            "message": f"Error: {str(e)}"
        }, status=500)
