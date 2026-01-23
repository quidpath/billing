"""
Payment Verification Service - Handle KES 1 verification and refunds
"""
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Optional, Dict
import logging

from ..models.payment_verification import PaymentVerification
from .payment_service import PaymentService
from .trial_service import TrialService

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for handling payment verification"""
    
    VERIFICATION_AMOUNT = Decimal('1.00')  # KES 1
    VERIFICATION_EXPIRY_MINUTES = 10  # Verification expires after 10 minutes
    
    @staticmethod
    def initiate_verification(
        corporate_id: str,
        corporate_name: str,
        phone_number: str,
        email: str,
        provider_config: Optional[Dict] = None
    ) -> Dict:
        """
        Initiate payment verification with KES 1
        Returns verification_id and STK push status
        """
        try:
            # Check if there's already a verified verification
            existing = PaymentVerification.objects.filter(
                corporate_id=corporate_id,
                status='verified'
            ).first()
            
            if existing and existing.verified_at:
                # Already verified within last 24 hours
                time_since_verification = timezone.now() - existing.verified_at
                if time_since_verification < timedelta(hours=24):
                    return {
                        'success': True,
                        'already_verified': True,
                        'verification_id': str(existing.id),
                        'message': 'Payment method already verified'
                    }
            
            # Create new verification record
            verification = PaymentVerification.objects.create(
                corporate_id=corporate_id,
                corporate_name=corporate_name,
                phone_number=phone_number,
                email=email,
                verification_amount=VerificationService.VERIFICATION_AMOUNT,
                status='pending',
                expires_at=timezone.now() + timedelta(minutes=VerificationService.VERIFICATION_EXPIRY_MINUTES)
            )
            
            # Create a temporary "verification invoice" (not a real invoice)
            # We'll use the payment service to initiate M-Pesa STK push
            from ..models.invoice import Invoice
            from ..models.plan import Plan
            
            # Get any active plan (we just need something for the invoice)
            plan = Plan.objects.filter(is_active=True).first()
            if not plan:
                return {
                    'success': False,
                    'message': 'No active plans available'
                }
            
            # Create a verification "invoice"
            temp_invoice = Invoice.objects.create(
                corporate_id=corporate_id,
                corporate_name=corporate_name,
                invoice_number=f'VRF-{verification.id.hex[:8].upper()}',
                status='pending',
                total_amount=VerificationService.VERIFICATION_AMOUNT,
                currency='KES',
                due_date=timezone.now().date() + timedelta(days=1),
                billing_period_start=timezone.now().date(),
                billing_period_end=timezone.now().date(),
                invoice_type='verification',
                metadata={
                    'verification_id': str(verification.id),
                    'is_verification': True,
                    'auto_refund': True
                }
            )
            
            # Initiate M-Pesa payment
            import os
            if not provider_config:
                provider_config = {
                    'consumer_key': os.environ.get('MPESA_CONSUMER_KEY', ''),
                    'consumer_secret': os.environ.get('MPESA_CONSUMER_SECRET', ''),
                    'business_short_code': os.environ.get('MPESA_SHORTCODE', '174379'),
                    'passkey': os.environ.get('MPESA_PASSKEY', ''),
                    'test_mode': os.environ.get('MPESA_TEST_MODE', 'true').lower() == 'true',
                    'callback_url': os.environ.get('MPESA_CALLBACK_URL', ''),
                }
            
            result = PaymentService.initiate_payment(
                invoice=temp_invoice,
                payment_method='mpesa',
                customer_email=email,
                customer_phone=phone_number,
                provider_config=provider_config
            )
            
            if result.get('success'):
                verification.payment_provider_reference = result.get('provider_reference')
                verification.provider_metadata = result
                verification.save()
                
                return {
                    'success': True,
                    'verification_id': str(verification.id),
                    'provider_reference': result.get('provider_reference'),
                    'message': 'Verification STK push sent. Please enter your M-Pesa PIN to complete verification.',
                    'amount': float(VerificationService.VERIFICATION_AMOUNT),
                    'expires_in_minutes': VerificationService.VERIFICATION_EXPIRY_MINUTES
                }
            else:
                verification.mark_as_failed(result.get('message', 'Failed to initiate verification payment'))
                temp_invoice.status = 'cancelled'
                temp_invoice.save()
                
                return {
                    'success': False,
                    'verification_id': str(verification.id),
                    'message': result.get('message', 'Failed to initiate verification')
                }
        
        except Exception as e:
            logger.error(f"Error initiating verification: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def handle_verification_payment_success(
        provider_reference: str,
        receipt_number: str,
        metadata: Dict
    ) -> Dict:
        """
        Handle successful verification payment
        Mark as verified and initiate refund
        """
        try:
            # Find verification by provider reference
            from ..models.payment import Payment
            payment = Payment.objects.filter(provider_reference=provider_reference).first()
            
            if not payment or not payment.invoice:
                logger.warning(f"Payment or invoice not found for reference {provider_reference}")
                return {
                    'success': False,
                    'message': 'Payment not found'
                }
            
            # Check if this is a verification invoice
            if not payment.invoice.metadata.get('is_verification'):
                logger.info(f"Not a verification payment: {provider_reference}")
                return {
                    'success': True,
                    'message': 'Not a verification payment'
                }
            
            verification_id = payment.invoice.metadata.get('verification_id')
            if not verification_id:
                logger.warning(f"No verification_id in invoice metadata")
                return {
                    'success': False,
                    'message': 'Verification ID not found'
                }
            
            verification = PaymentVerification.objects.filter(id=verification_id).first()
            if not verification:
                logger.warning(f"Verification not found: {verification_id}")
                return {
                    'success': False,
                    'message': 'Verification not found'
                }
            
            # Mark as verified
            verification.mark_as_verified(receipt_number, metadata)
            logger.info(f"Verification {verification_id} marked as verified")
            
            # Initiate refund
            refund_result = VerificationService.initiate_refund(verification)
            
            if refund_result.get('success'):
                logger.info(f"Refund initiated for verification {verification_id}")
                return {
                    'success': True,
                    'verification_id': str(verification.id),
                    'message': 'Verification successful, refund initiated'
                }
            else:
                logger.error(f"Failed to initiate refund for {verification_id}: {refund_result.get('message')}")
                # Still mark as verified, we'll retry refund later
                return {
                    'success': True,
                    'verification_id': str(verification.id),
                    'message': 'Verification successful, refund pending'
                }
        
        except Exception as e:
            logger.error(f"Error handling verification payment success: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def initiate_refund(verification: PaymentVerification) -> Dict:
        """
        Initiate refund for verification amount
        In sandbox, we'll just mark as refunded
        In production, use M-Pesa B2C API
        """
        try:
            import os
            test_mode = os.environ.get('MPESA_TEST_MODE', 'true').lower() == 'true'
            
            if test_mode:
                # In sandbox, we can't do real refunds, so just mark as refunded
                logger.info(f"Sandbox mode: Auto-marking verification {verification.id} as refunded")
                verification.mark_as_refunded(
                    refund_reference=f'RFND-{verification.id.hex[:8].upper()}',
                    refund_receipt='SANDBOX_REFUND',
                    metadata={'sandbox_mode': True, 'auto_refund': True}
                )
                return {
                    'success': True,
                    'message': 'Refund completed (sandbox mode)'
                }
            else:
                # In production, use M-Pesa B2C API for refund
                # This would require additional M-Pesa B2C setup
                # For now, mark as refunded and log for manual processing
                logger.info(f"Production mode: Marking verification {verification.id} for manual refund")
                verification.mark_as_refunded(
                    refund_reference=f'RFND-{verification.id.hex[:8].upper()}',
                    refund_receipt='PENDING_MANUAL_REFUND',
                    metadata={'requires_manual_refund': True, 'amount': float(verification.verification_amount)}
                )
                
                # TODO: Implement M-Pesa B2C refund API call here
                # For now, return success and handle refunds manually or via separate job
                
                return {
                    'success': True,
                    'message': 'Refund queued for processing'
                }
        
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def create_trial_after_verification(verification_id: str, plan_tier: str = 'starter') -> Dict:
        """
        Create trial after successful verification and refund
        """
        try:
            verification = PaymentVerification.objects.filter(id=verification_id).first()
            
            if not verification:
                return {
                    'success': False,
                    'message': 'Verification not found'
                }
            
            if not verification.can_create_trial():
                return {
                    'success': False,
                    'message': f'Cannot create trial. Verification status: {verification.status}'
                }
            
            # Create trial
            trial = TrialService.create_trial_for_corporate(
                corporate_id=str(verification.corporate_id),
                corporate_name=verification.corporate_name,
                plan_tier=plan_tier
            )
            
            # Update verification
            verification.trial_created = True
            verification.trial_id = trial.id
            verification.save()
            
            logger.info(f"Trial created for verification {verification_id}: {trial.id}")
            
            return {
                'success': True,
                'trial_id': str(trial.id),
                'verification_id': str(verification.id),
                'days_remaining': trial.days_remaining(),
                'message': '30-day free trial activated!'
            }
        
        except Exception as e:
            logger.error(f"Error creating trial after verification: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_verification_status(verification_id: str) -> Dict:
        """Get verification status"""
        try:
            verification = PaymentVerification.objects.filter(id=verification_id).first()
            
            if not verification:
                return {
                    'success': False,
                    'message': 'Verification not found'
                }
            
            # Check if expired
            if verification.status == 'pending' and verification.is_expired():
                verification.status = 'expired'
                verification.save()
            
            return {
                'success': True,
                'verification': {
                    'id': str(verification.id),
                    'status': verification.status,
                    'corporate_id': str(verification.corporate_id),
                    'phone_number': verification.phone_number,
                    'verification_amount': float(verification.verification_amount),
                    'verified_at': verification.verified_at.isoformat() if verification.verified_at else None,
                    'refunded_at': verification.refunded_at.isoformat() if verification.refunded_at else None,
                    'trial_created': verification.trial_created,
                    'trial_id': str(verification.trial_id) if verification.trial_id else None,
                    'can_create_trial': verification.can_create_trial(),
                    'failure_reason': verification.failure_reason,
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting verification status: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def handle_verification_payment_failed(provider_reference: str, reason: str) -> Dict:
        """
        Handle failed verification payment
        No refund needed since payment didn't go through
        """
        try:
            from ..models.payment import Payment
            payment = Payment.objects.filter(provider_reference=provider_reference).first()
            
            if not payment or not payment.invoice:
                return {
                    'success': False,
                    'message': 'Payment not found'
                }
            
            if not payment.invoice.metadata.get('is_verification'):
                return {
                    'success': True,
                    'message': 'Not a verification payment'
                }
            
            verification_id = payment.invoice.metadata.get('verification_id')
            if not verification_id:
                return {
                    'success': False,
                    'message': 'Verification ID not found'
                }
            
            verification = PaymentVerification.objects.filter(id=verification_id).first()
            if verification:
                verification.mark_as_failed(reason)
                logger.info(f"Verification {verification_id} marked as failed: {reason}")
            
            # Mark invoice as cancelled
            payment.invoice.status = 'cancelled'
            payment.invoice.save()
            
            return {
                'success': True,
                'verification_id': str(verification.id) if verification else None,
                'message': 'Verification failed, no charges applied'
            }
        
        except Exception as e:
            logger.error(f"Error handling verification payment failure: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
