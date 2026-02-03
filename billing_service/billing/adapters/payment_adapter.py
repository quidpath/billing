"""
Base payment adapter interface
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional


class PaymentAdapter(ABC):
    """Base class for payment gateway adapters"""

    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get("api_key")
        self.secret_key = config.get("secret_key")
        self.test_mode = config.get("test_mode", False)
        self.base_url = config.get("base_url")
        self.webhook_secret = config.get("webhook_secret")

    @abstractmethod
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
        pass

    @abstractmethod
    def verify_payment(self, provider_reference: str) -> Dict:
        pass

    @abstractmethod
    def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, headers: Dict) -> bool:
        pass
