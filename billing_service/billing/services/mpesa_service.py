"""
M-Pesa Daraja API service for billing
"""

import base64
import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class MpesaService:
    def __init__(self):
        self.consumer_key = getattr(settings, "MPESA_CONSUMER_KEY", "")
        self.consumer_secret = getattr(settings, "MPESA_CONSUMER_SECRET", "")
        self.business_short_code = getattr(settings, "MPESA_BUSINESS_SHORT_CODE", "9895960")
        self.till_number = getattr(settings, "MPESA_TILL_NUMBER", "9100097")
        self.passkey = getattr(settings, "MPESA_PASSKEY", "")
        self.callback_url = getattr(settings, "MPESA_CALLBACK_URL", "")
        self.environment = getattr(settings, "MPESA_ENVIRONMENT", "production")
        
        if self.environment == "sandbox":
            self.base_url = "https://sandbox.safaricom.co.ke"
        else:
            self.base_url = "https://api.safaricom.co.ke"
    
    def get_access_token(self) -> Optional[str]:
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json",
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            access_token = data.get("access_token")
            
            if access_token:
                logger.info("Successfully obtained M-Pesa access token")
                return access_token
            else:
                logger.error("No access token in response")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get M-Pesa access token: {str(e)}", exc_info=True)
            return None
    
    def generate_password(self, timestamp: str) -> str:
        data_to_encode = f"{self.business_short_code}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode()).decode()
        return encoded
    
    def generate_idempotency_key(self, entity_id: str, amount: float, timestamp: str) -> str:
        data = f"{entity_id}:{amount}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str,
        entity_id: str,
    ) -> Dict:
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token",
                }
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self.generate_password(timestamp)
            idempotency_key = self.generate_idempotency_key(entity_id, amount, timestamp)
            
            if not phone_number.startswith("254"):
                if phone_number.startswith("0"):
                    phone_number = "254" + phone_number[1:]
                elif phone_number.startswith("+254"):
                    phone_number = phone_number[1:]
                elif phone_number.startswith("254"):
                    pass
                else:
                    phone_number = "254" + phone_number
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": idempotency_key,
            }
            
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerBuyGoodsOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.till_number,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc,
            }
            
            logger.info(f"Initiating STK push for {phone_number}, Amount: {amount}, Idempotency: {idempotency_key}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ResponseCode") == "0":
                checkout_request_id = response_data.get("CheckoutRequestID")
                merchant_request_id = response_data.get("MerchantRequestID")
                
                logger.info(f"STK push sent successfully. CheckoutRequestID: {checkout_request_id}")
                
                return {
                    "success": True,
                    "message": "STK push sent successfully",
                    "checkout_request_id": checkout_request_id,
                    "merchant_request_id": merchant_request_id,
                    "idempotency_key": idempotency_key,
                }
            else:
                error_message = response_data.get("errorMessage", "Unknown error")
                logger.error(f"STK push failed: {error_message}")
                
                return {
                    "success": False,
                    "message": error_message,
                    "response": response_data,
                }
                
        except Exception as e:
            logger.error(f"STK push error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error initiating payment: {str(e)}",
            }
    
    def query_stk_status(self, checkout_request_id: str) -> Dict:
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    "success": False,
                    "message": "Failed to obtain access token",
                }
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self.generate_password(timestamp)
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id,
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            return {
                "success": True,
                "data": response_data,
            }
            
        except Exception as e:
            logger.error(f"STK query error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": f"Error querying payment status: {str(e)}",
            }
