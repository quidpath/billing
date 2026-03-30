"""
Paystack Payment Service
Handles all Paystack payment operations including card verification for corporate registration
"""
import logging
import os
from decimal import Decimal
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class PaystackService:
    """Service for Paystack payment operations"""
    
    def __init__(self):
        self.secret_key = os.environ.get("PAYSTACK_SECRET_KEY", "")
        self.public_key = os.environ.get("PAYSTACK_PUBLIC_KEY", "pk_live_2e38c2fb07042d05c08c4b4d3b4c8ce8f35d87c")
        self.test_mode = os.environ.get("PAYSTACK_TEST_MODE", "false").lower() == "true"
        self.base_url = "https://api.paystack.co"
        self.callback_url = os.environ.get("PAYSTACK_CALLBACK_URL", "")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for Paystack API"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
    
    def initialize_transaction(
        self,
        amount: Decimal,
        email: str,
        currency: str = "KES",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        channels: Optional[list] = None,
    ) -> Dict:
        """
        Initialize a Paystack transaction
        
        Args:
            amount: Amount in main currency unit (e.g., 1.00 KES)
            email: Customer email
            currency: Currency code (KES, NGN, USD, GHS, ZAR)
            callback_url: URL to redirect after payment
            metadata: Additional data to attach to transaction
            channels: Payment channels to enable (card, bank, ussd, mobile_money)
        
        Returns:
            Dict with success, reference, authorization_url, access_code
        """
        try:
            url = f"{self.base_url}/transaction/initialize"
            
            # Convert to smallest unit (kobo/cents)
            amount_in_kobo = int(float(amount) * 100)
            
            payload = {
                "amount": amount_in_kobo,
                "email": email,
                "currency": currency.upper(),
                "metadata": metadata or {},
            }
            
            if callback_url:
                payload["callback_url"] = callback_url
            elif self.callback_url:
                payload["callback_url"] = self.callback_url
            
            if channels:
                payload["channels"] = channels
            
            logger.info(f"Initializing Paystack transaction: {email}, {amount} {currency}")
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("status"):
                data = response_data.get("data", {})
                logger.info(f"Paystack transaction initialized: {data.get('reference')}")
                
                return {
                    "success": True,
                    "reference": data.get("reference"),
                    "authorization_url": data.get("authorization_url"),
                    "access_code": data.get("access_code"),
                    "message": "Transaction initialized successfully"
                }
            else:
                error_msg = response_data.get("message", "Failed to initialize transaction")
                logger.error(f"Paystack initialization failed: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
        
        except Exception as e:
            logger.error(f"Error initializing Paystack transaction: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def verify_transaction(self, reference: str) -> Dict:
        """
        Verify a Paystack transaction
        
        Args:
            reference: Paystack transaction reference
        
        Returns:
            Dict with success, status, amount, currency, customer, metadata
        """
        try:
            url = f"{self.base_url}/transaction/verify/{reference}"
            
            logger.info(f"Verifying Paystack transaction: {reference}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("status"):
                data = response_data.get("data", {})
                status = data.get("status", "").lower()
                
                # Convert amount from kobo to main unit
                amount = Decimal(str(data.get("amount", 0))) / 100
                
                logger.info(f"Transaction verified: {reference}, status: {status}")
                
                return {
                    "success": True,
                    "status": status,  # success, failed, abandoned
                    "amount": amount,
                    "currency": data.get("currency", "KES"),
                    "customer": {
                        "email": data.get("customer", {}).get("email"),
                        "phone": data.get("customer", {}).get("phone"),
                    },
                    "authorization": data.get("authorization", {}),
                    "metadata": data.get("metadata", {}),
                    "paid_at": data.get("paid_at"),
                    "reference": reference,
                }
            else:
                error_msg = response_data.get("message", "Verification failed")
                logger.error(f"Paystack verification failed: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
        
        except Exception as e:
            logger.error(f"Error verifying Paystack transaction: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def charge_authorization(
        self,
        authorization_code: str,
        email: str,
        amount: Decimal,
        currency: str = "KES",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Charge a saved authorization (recurring payment)
        
        Args:
            authorization_code: Authorization code from previous transaction
            email: Customer email
            amount: Amount to charge
            currency: Currency code
            metadata: Additional metadata
        
        Returns:
            Dict with success, reference, status, message
        """
        try:
            url = f"{self.base_url}/transaction/charge_authorization"
            
            amount_in_kobo = int(float(amount) * 100)
            
            payload = {
                "authorization_code": authorization_code,
                "email": email,
                "amount": amount_in_kobo,
                "currency": currency.upper(),
                "metadata": metadata or {},
            }
            
            logger.info(f"Charging authorization: {email}, {amount} {currency}")
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("status"):
                data = response_data.get("data", {})
                status = data.get("status", "").lower()
                
                logger.info(f"Authorization charged: {data.get('reference')}, status: {status}")
                
                return {
                    "success": True,
                    "reference": data.get("reference"),
                    "status": status,
                    "message": response_data.get("message", "Charge successful")
                }
            else:
                error_msg = response_data.get("message", "Charge failed")
                logger.error(f"Authorization charge failed: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
        
        except Exception as e:
            logger.error(f"Error charging authorization: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Paystack webhook signature
        
        Args:
            payload: Raw request body as bytes
            signature: x-paystack-signature header value
        
        Returns:
            bool indicating if signature is valid
        """
        import hashlib
        import hmac
        
        try:
            if not signature or not self.secret_key:
                return False
            
            expected_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
