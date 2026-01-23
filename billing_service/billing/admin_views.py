"""
Admin API Views - For main backend admin integration
These endpoints allow the main backend to fetch billing data for admin panel
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import Plan, Trial, Subscription, Invoice, Payment, Promotion
from .services import TrialService, SubscriptionService


@csrf_exempt
def list_all_trials(request):
    """List all trials - for admin viewing"""
    try:
        # Get query params for filtering
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        
        trials = Trial.objects.all()
        if status:
            trials = trials.filter(status=status)
        
        trials = trials.order_by('-created_at')[:limit]
        
        trials_data = [{
            'id': str(t.id),
            'corporate_id': str(t.corporate_id),
            'corporate_name': t.corporate_name,
            'plan_tier': t.plan.tier if t.plan else None,
            'status': t.status,
            'start_date': t.start_date.isoformat(),
            'end_date': t.end_date.isoformat(),
            'days_remaining': t.days_remaining(),
            'created_at': t.created_at.isoformat(),
        } for t in trials]
        
        return JsonResponse({
            'success': True,
            'data': {'trials': trials_data, 'count': len(trials_data)}
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def list_all_subscriptions(request):
    """List all subscriptions - for admin viewing"""
    try:
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        
        subscriptions = Subscription.objects.select_related('plan').all()
        if status:
            subscriptions = subscriptions.filter(status=status)
        
        subscriptions = subscriptions.order_by('-created_at')[:limit]
        
        subscriptions_data = [{
            'id': str(s.id),
            'corporate_id': str(s.corporate_id),
            'corporate_name': s.corporate_name,
            'plan_name': s.plan.name,
            'plan_tier': s.plan.tier,
            'status': s.status,
            'billing_cycle': s.billing_cycle,
            'total_amount': float(s.total_amount),
            'currency': s.currency,
            'start_date': s.start_date.isoformat(),
            'end_date': s.end_date.isoformat(),
            'created_at': s.created_at.isoformat(),
        } for s in subscriptions]
        
        return JsonResponse({
            'success': True,
            'data': {'subscriptions': subscriptions_data, 'count': len(subscriptions_data)}
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def list_all_invoices(request):
    """List all invoices - for admin viewing"""
    try:
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        
        invoices = Invoice.objects.all()
        if status:
            invoices = invoices.filter(status=status)
        
        invoices = invoices.order_by('-created_at')[:limit]
        
        invoices_data = [{
            'id': str(inv.id),
            'corporate_id': str(inv.corporate_id),
            'corporate_name': inv.corporate_name,
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'total_amount': float(inv.total_amount),
            'currency': inv.currency,
            'due_date': inv.due_date.isoformat(),
            'paid_at': inv.paid_at.isoformat() if inv.paid_at else None,
            'created_at': inv.created_at.isoformat(),
        } for inv in invoices]
        
        return JsonResponse({
            'success': True,
            'data': {'invoices': invoices_data, 'count': len(invoices_data)}
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def list_all_payments(request):
    """List all payments - for admin viewing"""
    try:
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        
        payments = Payment.objects.select_related('invoice').all()
        if status:
            payments = payments.filter(status=status)
        
        payments = payments.order_by('-created_at')[:limit]
        
        payments_data = [{
            'id': str(p.id),
            'corporate_id': str(p.corporate_id),
            'corporate_name': p.corporate_name,
            'invoice_number': p.invoice.invoice_number if p.invoice else None,
            'amount': float(p.amount),
            'currency': p.currency,
            'payment_method': p.payment_method,
            'status': p.status,
            'provider': p.provider,
            'transaction_id': p.transaction_id,
            'paid_at': p.paid_at.isoformat() if p.paid_at else None,
            'created_at': p.created_at.isoformat(),
        } for p in payments]
        
        return JsonResponse({
            'success': True,
            'data': {'payments': payments_data, 'count': len(payments_data)}
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def get_billing_stats(request):
    """Get overall billing statistics - for admin dashboard"""
    try:
        from django.db.models import Count, Sum
        
        stats = {
            'trials': {
                'total': Trial.objects.count(),
                'active': Trial.objects.filter(status='active').count(),
                'expired': Trial.objects.filter(status='expired').count(),
                'converted': Trial.objects.filter(status='converted').count(),
            },
            'subscriptions': {
                'total': Subscription.objects.count(),
                'active': Subscription.objects.filter(status='active').count(),
                'cancelled': Subscription.objects.filter(status='cancelled').count(),
                'pending': Subscription.objects.filter(status='pending').count(),
            },
            'invoices': {
                'total': Invoice.objects.count(),
                'pending': Invoice.objects.filter(status='pending').count(),
                'paid': Invoice.objects.filter(status='paid').count(),
                'overdue': Invoice.objects.filter(status='overdue').count(),
                'total_amount': float(Invoice.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'pending_amount': float(Invoice.objects.filter(status__in=['pending', 'overdue']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
            },
            'payments': {
                'total': Payment.objects.count(),
                'completed': Payment.objects.filter(status='completed').count(),
                'pending': Payment.objects.filter(status='pending').count(),
                'failed': Payment.objects.filter(status='failed').count(),
                'total_amount': float(Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
            },
            'revenue': {
                'total': float(Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
                'this_month': 0,  # TODO: Calculate current month revenue
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': stats
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@csrf_exempt
def get_corporate_billing_summary(request, corporate_id):
    """Get billing summary for a specific corporate - for admin viewing"""
    try:
        from django.db.models import Sum
        
        # Get trial status
        trial = Trial.objects.filter(corporate_id=corporate_id).order_by('-created_at').first()
        trial_data = None
        if trial:
            trial_data = {
                'id': str(trial.id),
                'status': trial.status,
                'days_remaining': trial.days_remaining(),
                'end_date': trial.end_date.isoformat(),
            }
        
        # Get active subscription
        subscription = Subscription.objects.filter(
            corporate_id=corporate_id,
            status='active'
        ).select_related('plan').first()
        subscription_data = None
        if subscription:
            subscription_data = {
                'id': str(subscription.id),
                'plan_name': subscription.plan.name,
                'plan_tier': subscription.plan.tier,
                'billing_cycle': subscription.billing_cycle,
                'total_amount': float(subscription.total_amount),
                'end_date': subscription.end_date.isoformat(),
            }
        
        # Get invoices
        invoices = Invoice.objects.filter(corporate_id=corporate_id).order_by('-created_at')[:10]
        invoices_data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'status': inv.status,
            'total_amount': float(inv.total_amount),
            'due_date': inv.due_date.isoformat(),
        } for inv in invoices]
        
        # Get payments
        payments = Payment.objects.filter(corporate_id=corporate_id).order_by('-created_at')[:10]
        payments_data = [{
            'id': str(p.id),
            'amount': float(p.amount),
            'status': p.status,
            'payment_method': p.payment_method,
            'paid_at': p.paid_at.isoformat() if p.paid_at else None,
        } for p in payments]
        
        # Calculate totals
        total_invoiced = float(Invoice.objects.filter(
            corporate_id=corporate_id
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
        
        total_paid = float(Payment.objects.filter(
            corporate_id=corporate_id,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0)
        
        return JsonResponse({
            'success': True,
            'data': {
                'corporate_id': str(corporate_id),
                'trial': trial_data,
                'subscription': subscription_data,
                'invoices': invoices_data,
                'payments': payments_data,
                'totals': {
                    'invoiced': total_invoiced,
                    'paid': total_paid,
                    'outstanding': total_invoiced - total_paid,
                }
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


