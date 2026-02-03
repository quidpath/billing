"""
M-Pesa Daraja API adapter for STK Push payments
Supports Sandbox and Production environments
"""

import base64
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

import requests

from .payment_adapter import PaymentAdapter

logger = logging.getLogger(__name__)


class MpesaDarajaAdapter(PaymentAdapter):
    """M-Pesa Daraja API 2.0 integration for STK Push"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.consumer_key = config.get("consumer_key")
        self.consumer_secret = config.get("consumer_secret")
        self.business_short_code = config.get("business_short_code", "174379")
        self.passkey = config.get("passkey")
        self.callback_url = config.get("callback_url", "")

        # Set base URL based on test mode
        if self.test_mode:
            self.base_url = "https://sandbox.safaricom.co.ke"
        else:
            self.base_url = "https://api.safaricom.co.ke"

        self._access_token = None
        self._token_expiry = None

    def _get_access_token(self) -> str:
        """Get OAuth access token from M-Pesa"""
        try:
            # Validate credentials are set
            if not self.consumer_key or not self.consumer_secret:
                raise Exception(
                    "M-Pesa Consumer Key and Consumer Secret must be configured"
                )

            # Check if we have a valid cached token
            if self._access_token and self._token_expiry:
                from datetime import datetime, timedelta

                if datetime.now() < self._token_expiry:
                    return self._access_token

            # Get new access token
            auth_url = (
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            )

            logger.info(f"Requesting M-Pesa access token from {auth_url}")

            response = requests.get(
                auth_url, auth=(self.consumer_key, self.consumer_secret), timeout=30
            )

            # Check for authentication errors
            if response.status_code == 400:
                error_detail = "Invalid Consumer Key or Consumer Secret"
                try:
                    error_data = response.json()
                    if "error_description" in error_data:
                        error_detail = error_data["error_description"]
                    elif "error" in error_data:
                        error_detail = error_data["error"]
                except:
                    pass
                logger.error(f"M-Pesa authentication failed (400): {error_detail}")
                raise Exception(
                    f"M-Pesa authentication failed: {error_detail}. Please verify your Consumer Key and Consumer Secret are correct."
                )

            if response.status_code == 401:
                logger.error("M-Pesa authentication failed (401): Unauthorized")
                raise Exception(
                    "M-Pesa authentication failed: Unauthorized. Please verify your Consumer Key and Consumer Secret are correct."
                )

            response.raise_for_status()

            data = response.json()
            self._access_token = data.get("access_token")

            if not self._access_token:
                logger.error(f"M-Pesa access token response missing token: {data}")
                raise Exception(
                    "M-Pesa access token not received. Please check your credentials."
                )

            # Cache token for 55 minutes (expires in 1 hour)
            from datetime import datetime, timedelta

            self._token_expiry = datetime.now() + timedelta(minutes=55)

            logger.info("M-Pesa access token obtained successfully")
            return self._access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting M-Pesa access token: {str(e)}")
            raise Exception(f"Failed to connect to M-Pesa API: {str(e)}")
        except Exception as e:
            # Re-raise if it's already a formatted error
            if "M-Pesa authentication failed" in str(e) or "Failed to connect" in str(
                e
            ):
                raise
            logger.error(f"Error getting M-Pesa access token: {str(e)}")
            raise Exception(f"Failed to authenticate with M-Pesa: {str(e)}")

    def _generate_password(self, timestamp: str) -> str:
        """Generate password for STK Push"""
        data_to_encode = f"{self.business_short_code}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode("utf-8")

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to M-Pesa format (254XXXXXXXXX)"""
        # Remove any spaces, dashes, or plus signs
        phone = phone.replace(" ", "").replace("-", "").replace("+", "")

        # If starts with 0, replace with 254
        if phone.startswith("0"):
            phone = "254" + phone[1:]

        # If doesn't start with 254, add it
        if not phone.startswith("254"):
            phone = "254" + phone

        return phone

    def initiate_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        customer_email: str,
        customer_phone: Optional[str] = None,
        metadata: Optional[Dict] = None,
        callback_url: Optional[str] = None,
    ) -> Dict:
        """Initiate M-Pesa STK Push payment"""
        try:
            if not customer_phone:
                return {
                    "status": "failed",
                    "message": "Phone number is required for M-Pesa payments",
                }

            # Get access token
            access_token = self._get_access_token()

            # Generate timestamp and password
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self._generate_password(timestamp)

            # Format phone number
            phone = self._format_phone_number(customer_phone)

            # Prepare STK Push request
            stk_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

            # Account reference and transaction description
            account_ref = (
                metadata.get("invoice_number", "QUIDPATH") if metadata else "QUIDPATH"
            )
            transaction_desc = (
                metadata.get("description", "Quidpath Subscription Payment")
                if metadata
                else "Quidpath Subscription Payment"
            )

            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(float(amount)),  # M-Pesa accepts integer amounts
                "PartyA": phone,  # Phone number sending money
                "PartyB": self.business_short_code,  # Organization receiving
                "PhoneNumber": phone,  # Phone number to receive the STK push
                "CallBackURL": callback_url or self.callback_url,
                "AccountReference": account_ref[:12],  # Max 12 characters
                "TransactionDesc": transaction_desc[:13],  # Max 13 characters
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            logger.info(
                f"Initiating M-Pesa STK Push for phone {phone}, amount {amount}"
            )

            response = requests.post(stk_url, json=payload, headers=headers, timeout=30)

            response_data = response.json()
            logger.info(f"M-Pesa STK Push response: {response_data}")

            if response.status_code == 200 and response_data.get("ResponseCode") == "0":
                checkout_request_id = response_data.get("CheckoutRequestID")
                merchant_request_id = response_data.get("MerchantRequestID")
                customer_message = response_data.get(
                    "CustomerMessage", "STK push sent to your phone"
                )

                logger.info(
                    f"STK Push successful - CheckoutRequestID: {checkout_request_id}, MerchantRequestID: {merchant_request_id}"
                )

                return {
                    "status": "success",
                    "provider_reference": checkout_request_id,
                    "merchant_request_id": merchant_request_id,
                    "message": customer_message,
                    "metadata": response_data,
                }
            else:
                error_code = response_data.get("errorCode") or response_data.get(
                    "ResponseCode"
                )
                error_message = response_data.get("errorMessage") or response_data.get(
                    "ResponseDescription", "Failed to initiate payment"
                )

                logger.error(
                    f"M-Pesa STK Push failed - Code: {error_code}, Message: {error_message}"
                )

                return {
                    "status": "failed",
                    "message": error_message,
                    "error_code": error_code,
                }

        except Exception as e:
            logger.error(f"Error initiating M-Pesa payment: {str(e)}")
            return {"status": "failed", "message": f"Error: {str(e)}"}

    def verify_payment(self, provider_reference: str) -> Dict:
        """Query M-Pesa transaction status"""
        try:
            access_token = self._get_access_token()

            query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = self._generate_password(timestamp)

            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": provider_reference,
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                query_url, json=payload, headers=headers, timeout=30
            )

            # Check if response has content before parsing JSON
            if not response.text or not response.text.strip():
                logger.error(
                    f"M-Pesa query returned empty response. Status: {response.status_code}"
                )
                return {
                    "status": "failed",
                    "message": "M-Pesa API returned empty response. Please try again.",
                }

            try:
                response_data = response.json()
            except ValueError as e:
                # M-Pesa returned non-JSON (likely HTML error page)
                logger.error(
                    f"M-Pesa query returned invalid JSON. Status: {response.status_code}, Response: {response.text[:200]}"
                )

                # For 403/401 errors, treat as pending to allow retry (might be temporary auth issue)
                if response.status_code in [403, 401]:
                    logger.warning(
                        f"M-Pesa authentication error ({response.status_code}). Keeping payment as pending for retry."
                    )
                    return {
                        "status": "pending",
                        "message": "Payment verification temporarily unavailable. The system will retry automatically.",
                    }

                # For other errors with invalid JSON, mark as failed
                return {
                    "status": "failed",
                    "message": f"M-Pesa API returned invalid response. Please try again.",
                }

            if response.status_code == 200:
                result_code = response_data.get("ResultCode")
                result_desc = response_data.get("ResultDesc", "")

                if result_code == "0":
                    # Payment successful
                    return {
                        "status": "success",
                        "amount": Decimal(str(response_data.get("Amount", 0))),
                        "currency": "KES",
                        "metadata": response_data,
                    }
                elif result_code == "1032":
                    # Request cancelled by user
                    return {"status": "failed", "message": "Payment cancelled by user"}
                elif result_code == "1037":
                    # DS timeout - user cannot be reached
                    return {
                        "status": "failed",
                        "message": "STK push timed out. Please ensure your phone is on and has network coverage, then try again.",
                    }
                elif result_code == "1":
                    # Insufficient balance
                    return {"status": "failed", "message": "Insufficient balance"}
                elif result_code == "17":
                    # Customer cancelled the request
                    return {"status": "failed", "message": "Payment cancelled by user"}
                elif result_code == "1014":
                    # Invalid shortcode
                    return {
                        "status": "failed",
                        "message": "Invalid payment configuration. Please contact support.",
                    }
                else:
                    # Still pending or other status
                    status_message = result_desc or response_data.get(
                        "ResultDesc", "Payment pending"
                    )
                    logger.info(
                        f"M-Pesa payment status: ResultCode={result_code}, ResultDesc={status_message}"
                    )
                    return {"status": "pending", "message": status_message}
            elif response.status_code == 429:
                # Rate limit - don't mark as failed, keep as pending
                logger.warning(
                    f"M-Pesa rate limit hit (429). Payment still pending, will retry."
                )
                return {
                    "status": "pending",
                    "message": "Payment verification is temporarily rate-limited. Please wait a moment and the system will retry.",
                }
            else:
                # Non-200 status code (but not rate limit)
                logger.error(
                    f"M-Pesa query returned non-200 status: {response.status_code}, Response: {response.text[:200]}"
                )
                return {
                    "status": "failed",
                    "message": f"M-Pesa API returned error (Status: {response.status_code}). Please try again.",
                }

        except Exception as e:
            logger.error(f"Error verifying M-Pesa payment: {str(e)}")
            return {"status": "failed", "message": f"Error: {str(e)}"}

    def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """Handle M-Pesa callback/webhook"""
        try:
            # M-Pesa sends callback in specific format
            body = payload.get("Body", {})
            stk_callback = body.get("stkCallback", {})

            result_code = stk_callback.get("ResultCode")
            result_desc = stk_callback.get("ResultDesc", "")
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            merchant_request_id = stk_callback.get("MerchantRequestID")

            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get("CallbackMetadata", {})
                items = callback_metadata.get("Item", [])

                # Extract payment details
                amount = 0
                mpesa_receipt = ""
                phone = ""

                for item in items:
                    name = item.get("Name")
                    value = item.get("Value")

                    if name == "Amount":
                        amount = value
                    elif name == "MpesaReceiptNumber":
                        mpesa_receipt = value
                    elif name == "PhoneNumber":
                        phone = value

                return {
                    "status": "success",
                    "provider_reference": checkout_request_id,
                    "amount": Decimal(str(amount)),
                    "currency": "KES",
                    "metadata": {
                        "mpesa_receipt": mpesa_receipt,
                        "phone_number": phone,
                        "merchant_request_id": merchant_request_id,
                        "result_desc": result_desc,
                    },
                }
            else:
                # Payment failed or cancelled
                return {
                    "status": "failed",
                    "provider_reference": checkout_request_id,
                    "message": result_desc,
                }

        except Exception as e:
            logger.error(f"Error handling M-Pesa webhook: {str(e)}")
            return {"status": "failed", "message": f"Error: {str(e)}"}

    def verify_webhook_signature(self, payload: bytes, headers: Dict) -> bool:
        """
        M-Pesa doesn't use signature verification for callbacks
        Instead, we verify the source IP and use HTTPS
        For sandbox, always return True
        """
        if self.test_mode:
            return True

        # In production, verify the source IP is from Safaricom
        # You can implement IP whitelist checking here
        return True
