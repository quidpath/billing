"""
Webhook Service for sending subscription events to Main Backend
"""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for sending webhook events to Main Backend
    """

    def __init__(self):
        self.erp_backend_url = settings.ERP_BACKEND_URL
        self.webhook_secret = settings.BILLING_WEBHOOK_SECRET
        self.webhook_endpoint = (
            f"{self.erp_backend_url}/webhooks/subscription"
        )

    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for webhook payload
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.webhook_secret.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def send_webhook(self, event_type: str, subscription_data: Dict[str, Any]) -> bool:
        """
        Send webhook event to Main Backend

        Args:
            event_type: Type of event (subscription.created, subscription.activated, etc.)
            subscription_data: Subscription data to send

        Returns:
            bool: True if webhook sent successfully, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("BILLING_WEBHOOK_SECRET not configured, skipping webhook")
            return False

        payload = {"event": event_type, "data": subscription_data}

        signature = self._generate_signature(payload)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        }

        try:
            response = requests.post(
                self.webhook_endpoint, json=payload, headers=headers, timeout=10
            )

            if response.status_code == 200:
                logger.info(
                    f"Webhook sent successfully: {event_type} for subscription {subscription_data.get('id')}"
                )
                return True
            else:
                logger.error(
                    f"Webhook failed: {event_type} - Status {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request failed: {event_type} - {str(e)}")
            return False

    def send_subscription_created(self, subscription):
        """Send subscription.created event"""
        data = self._serialize_subscription(subscription)
        return self.send_webhook("subscription.created", data)

    def send_subscription_activated(self, subscription):
        """Send subscription.activated event"""
        data = self._serialize_subscription(subscription)
        return self.send_webhook("subscription.activated", data)

    def send_subscription_cancelled(self, subscription):
        """Send subscription.cancelled event"""
        data = self._serialize_subscription(subscription)
        return self.send_webhook("subscription.cancelled", data)

    def send_subscription_expired(self, subscription):
        """Send subscription.expired event"""
        data = self._serialize_subscription(subscription)
        return self.send_webhook("subscription.expired", data)

    def send_subscription_upgraded(self, subscription, old_plan_name: str):
        """Send subscription.upgraded event"""
        data = self._serialize_subscription(subscription)
        data["old_plan_name"] = old_plan_name
        return self.send_webhook("subscription.upgraded", data)

    def send_subscription_downgraded(self, subscription, old_plan_name: str):
        """Send subscription.downgraded event"""
        data = self._serialize_subscription(subscription)
        data["old_plan_name"] = old_plan_name
        return self.send_webhook("subscription.downgraded", data)

    def send_payment_succeeded(self, subscription, payment_data: Dict[str, Any]):
        """Send payment.succeeded event"""
        data = self._serialize_subscription(subscription)
        data["payment"] = payment_data
        return self.send_webhook("payment.succeeded", data)

    def send_payment_failed(self, subscription, payment_data: Dict[str, Any]):
        """Send payment.failed event"""
        data = self._serialize_subscription(subscription)
        data["payment"] = payment_data
        return self.send_webhook("payment.failed", data)

    def _serialize_subscription(self, subscription) -> Dict[str, Any]:
        """Serialize subscription model to dictionary for webhook payload"""
        return {
            "subscription_id": str(subscription.id),
            "corporate_id": str(subscription.corporate_id),
            "corporate_name": subscription.corporate_name,
            "plan": {
                "id": str(subscription.plan.id),
                "name": subscription.plan.name,
                "tier": subscription.plan.tier,
                "plan_type": subscription.plan.plan_type,
            },
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "trial_start_date": (
                subscription.trial_start_date.isoformat()
                if subscription.trial_start_date
                else None
            ),
            "trial_end_date": (
                subscription.trial_end_date.isoformat()
                if subscription.trial_end_date
                else None
            ),
            "auto_renew": subscription.auto_renew,
            "total_amount": float(subscription.total_amount),
            "currency": subscription.currency,
            "new_end_date": subscription.end_date.isoformat(),
        }


webhook_service = WebhookService()
