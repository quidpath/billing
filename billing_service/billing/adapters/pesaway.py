"""
Pesaway payment gateway adapter
"""
import requests
import hmac
import hashlib
import json
from decimal import Decimal
from typing import Dict, Optional

from .payment_adapter import PaymentAdapter


class PesawayAdapter(PaymentAdapter):
    """Pesaway payment gateway integration"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.merchant_id = config.get('merchant_id')
        self.api_key = config.get('api_key') or config.get('public_key')
        self.secret_key = config.get('secret_key') or config.get('private_key')
        self.base_url = config.get('base_url') or (
            'https://api.pesaway.com' if not self.test_mode else 'https://sandbox.pesaway.com'
        )
        self.callback_url = config.get('callback_url', '')
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Merchant-ID': self.merchant_id or '',
        }
    
    def initiate_payment(self, amount: Decimal, currency: str, payment_method: str,
                        customer_email: str, customer_phone: Optional[str] = None,
                        metadata: Optional[Dict] = None, callback_url: Optional[str] = None) -> Dict:
        try:
            url = f"{self.base_url}/api/v1/payments/initiate"
            payload = {
                'amount': str(float(amount)),
                'currency': currency.upper(),
                'payment_method': payment_method,
                'customer_email': customer_email,
                'callback_url': callback_url or self.callback_url,
                'metadata': metadata or {},
            }
            if payment_method in ['mpesa', 'airtel_money']:
                if not customer_phone:
                    return {'status': 'failed', 'message': f'{payment_method.upper()} requires customer phone number'}
                payload['customer_phone'] = customer_phone
            
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('success'):
                return {
                    'status': 'success',
                    'provider_reference': response_data.get('transaction_id') or response_data.get('reference'),
                    'checkout_url': response_data.get('checkout_url'),
                    'message': response_data.get('message', 'Payment initiated successfully'),
                    'metadata': response_data,
                }
            else:
                return {
                    'status': 'failed',
                    'message': response_data.get('message', 'Failed to initiate payment'),
                }
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def verify_payment(self, provider_reference: str) -> Dict:
        try:
            url = f"{self.base_url}/api/v1/payments/verify/{provider_reference}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('success'):
                payment_data = response_data.get('data', {})
                return {
                    'status': 'success' if payment_data.get('status') == 'completed' else 'pending',
                    'amount': Decimal(str(payment_data.get('amount', 0))),
                    'currency': payment_data.get('currency', 'KES'),
                    'metadata': payment_data,
                }
            return {'status': 'failed', 'message': 'Payment verification failed'}
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        try:
            event_type = payload.get('event_type') or payload.get('type')
            payment_data = payload.get('data') or payload.get('payment') or payload
            
            if event_type not in ['payment.completed', 'payment.success', 'payment.failed']:
                return {'status': 'ignored', 'message': f'Unhandled event type: {event_type}'}
            
            transaction_id = payment_data.get('transaction_id') or payment_data.get('reference')
            status = payment_data.get('status', '').lower()
            
            if status in ['completed', 'success', 'successful']:
                return {
                    'status': 'success',
                    'provider_reference': transaction_id,
                    'amount': Decimal(str(payment_data.get('amount', 0))),
                    'currency': payment_data.get('currency', 'KES'),
                    'metadata': payment_data,
                }
            elif status in ['failed', 'cancelled']:
                return {
                    'status': 'failed',
                    'provider_reference': transaction_id,
                    'message': payment_data.get('message', 'Payment failed'),
                }
            return {'status': 'pending', 'provider_reference': transaction_id}
        except Exception as e:
            return {'status': 'failed', 'message': f'Error: {str(e)}'}
    
    def verify_webhook_signature(self, payload: bytes, headers: Dict) -> bool:
        try:
            signature = headers.get('X-Pesaway-Signature') or headers.get('X-Signature')
            if not signature or not self.webhook_secret:
                return False
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False








