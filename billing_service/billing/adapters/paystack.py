"""
Paystack payment gateway adapter
"""
import requests
import hmac
import hashlib
import json
from decimal import Decimal
from typing import Dict, Optional

from .payment_adapter import PaymentAdapter


class PaystackAdapter(PaymentAdapter):
    """Paystack payment gateway integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key') or config.get('api_key')
        self.base_url = config.get('base_url') or (
            'https://api.paystack.co' if not self.test_mode else 'https://api.paystack.co'
        )
        self.callback_url = config.get('callback_url', '')
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initiate_payment(self, amount: Decimal, currency: str, payment_method: str,
                        customer_email: str, customer_phone: Optional[str] = None,
                        metadata: Optional[Dict] = None, callback_url: Optional[str] = None) -> Dict:
        """
        Initiate a payment transaction
        
        Args:
            amount: Amount in smallest currency unit (kobo for NGN, cents for USD, etc.)
            currency: Currency code (NGN, USD, GHS, ZAR, KES)
            payment_method: Payment method (not directly used by Paystack initialize endpoint)
            customer_email: Customer's email address
            customer_phone: Customer's phone number (optional)
            metadata: Additional metadata for the transaction
            callback_url: URL to redirect after payment
            
        Returns:
            Dict with status, provider_reference, checkout_url, message, and metadata
        """
        try:
            url = f"{self.base_url}/transaction/initialize"
            
            # Convert amount to kobo/cents (smallest currency unit)
            amount_in_kobo = int(float(amount) * 100)
            
            payload = {
                'amount': amount_in_kobo,
                'currency': currency.upper(),
                'email': customer_email,
                'callback_url': callback_url or self.callback_url,
                'metadata': metadata or {},
            }
            
            # Add channels if payment method specified
            if payment_method == 'mobile_money':
                payload['channels'] = ['mobile_money']
            elif payment_method == 'bank':
                payload['channels'] = ['bank']
            elif payment_method == 'card':
                payload['channels'] = ['card']
            elif payment_method == 'ussd':
                payload['channels'] = ['ussd']
            
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                return {
                    'status': 'success',
                    'provider_reference': data.get('reference'),
                    'checkout_url': data.get('authorization_url'),
                    'message': response_data.get('message', 'Payment initiated successfully'),
                    'metadata': data,
                }
            else:
                return {
                    'status': 'failed',
                    'message': response_data.get('message', 'Failed to initiate payment'),
                }
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def verify_payment(self, provider_reference: str) -> Dict:
        """
        Verify a payment transaction
        
        Args:
            provider_reference: Paystack transaction reference
            
        Returns:
            Dict with status, amount, currency, and metadata
        """
        try:
            url = f"{self.base_url}/transaction/verify/{provider_reference}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                status = data.get('status', '').lower()
                
                # Convert amount from kobo/cents back to main currency unit
                amount_in_main_unit = Decimal(str(data.get('amount', 0))) / 100
                
                return {
                    'status': 'success' if status == 'success' else 'pending' if status == 'pending' else 'failed',
                    'amount': amount_in_main_unit,
                    'currency': data.get('currency', 'NGN'),
                    'metadata': data,
                }
            return {'status': 'failed', 'message': 'Payment verification failed'}
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """
        Handle webhook from Paystack
        
        Args:
            payload: Webhook payload
            headers: Request headers
            
        Returns:
            Dict with status, provider_reference, amount, currency, and metadata
        """
        try:
            event_type = payload.get('event')
            data = payload.get('data', {})
            
            # Handle only charge.success and charge.failed events
            if event_type not in ['charge.success', 'charge.failed']:
                return {'status': 'ignored', 'message': f'Unhandled event type: {event_type}'}
            
            reference = data.get('reference')
            status = data.get('status', '').lower()
            
            # Convert amount from kobo/cents to main currency unit
            amount_in_main_unit = Decimal(str(data.get('amount', 0))) / 100
            
            if status == 'success':
                return {
                    'status': 'success',
                    'provider_reference': reference,
                    'amount': amount_in_main_unit,
                    'currency': data.get('currency', 'NGN'),
                    'metadata': data,
                }
            elif status == 'failed':
                return {
                    'status': 'failed',
                    'provider_reference': reference,
                    'message': data.get('gateway_response', 'Payment failed'),
                }
            return {'status': 'pending', 'provider_reference': reference}
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def verify_webhook_signature(self, payload: bytes, headers: Dict) -> bool:
        """
        Verify webhook signature from Paystack
        
        Args:
            payload: Raw request body as bytes
            headers: Request headers
            
        Returns:
            bool indicating if signature is valid
        """
        try:
            signature = headers.get('x-paystack-signature') or headers.get('X-Paystack-Signature')
            if not signature or not self.secret_key:
                return False
            
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False
    
    def initiate_mobile_money(self, amount: Decimal, currency: str, customer_email: str,
                             customer_phone: str, provider: str, metadata: Optional[Dict] = None,
                             callback_url: Optional[str] = None) -> Dict:
        """
        Initiate mobile money payment (MTN, Vodafone, AirtelTigo for GHS)
        
        Args:
            amount: Amount to charge
            currency: Currency code (GHS for Ghana mobile money)
            customer_email: Customer's email
            customer_phone: Customer's phone number
            provider: Mobile money provider (mtn, vod, tgo)
            metadata: Additional metadata
            callback_url: Callback URL
            
        Returns:
            Dict with payment initiation result
        """
        try:
            url = f"{self.base_url}/charge"
            
            # Convert amount to pesewas for GHS
            amount_in_pesewas = int(float(amount) * 100)
            
            payload = {
                'amount': amount_in_pesewas,
                'currency': currency.upper(),
                'email': customer_email,
                'mobile_money': {
                    'phone': customer_phone,
                    'provider': provider
                },
                'metadata': metadata or {},
            }
            
            if callback_url:
                payload['callback_url'] = callback_url
            
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status'):
                data = response_data.get('data', {})
                return {
                    'status': 'success',
                    'provider_reference': data.get('reference'),
                    'message': response_data.get('message', 'Mobile money payment initiated'),
                    'metadata': data,
                }
            else:
                return {
                    'status': 'failed',
                    'message': response_data.get('message', 'Failed to initiate mobile money payment'),
                }
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}



