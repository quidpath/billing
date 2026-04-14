"""
Transaction Logger for Billing Service
Provides comprehensive logging for all billing operations
"""
import logging
import uuid
from decimal import Decimal
from typing import Optional, Dict, Any

from django.db import transaction
from django.http import HttpRequest

from ..models.transaction_log import State, TransactionType, BillingTransaction, AuditLog

logger = logging.getLogger(__name__)


class TransactionLogger:
    """
    Logs all billing transactions and operations
    Similar to TransactionLogBase in main backend
    """

    @classmethod
    def log(
        cls,
        transaction_type: str,
        corporate_id: Optional[str] = None,
        corporate_name: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        payment_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: str = "KES",
        message: str = "",
        state_name: str = "Active",
        provider: Optional[str] = None,
        provider_reference: Optional[str] = None,
        response_code: Optional[str] = None,
        response_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        webhook_response: Optional[str] = None,
        request: Optional[HttpRequest] = None,
    ) -> Optional[BillingTransaction]:
        """
        Log a billing transaction
        
        Args:
            transaction_type: Type of transaction (e.g., 'PAYMENT_SUCCESS', 'INVOICE_CREATED')
            corporate_id: Corporate/Organization UUID
            corporate_name: Corporate/Organization name
            user_id: User UUID (if applicable)
            user_email: User email (if applicable)
            payment_id: Payment UUID (if applicable)
            invoice_id: Invoice UUID (if applicable)
            subscription_id: Subscription UUID (if applicable)
            amount: Transaction amount
            currency: Currency code (default: KES)
            message: Log message
            state_name: State name (Active, Completed, Failed, etc.)
            provider: Payment provider (paystack, mpesa, etc.)
            provider_reference: Provider transaction reference
            response_code: Response code from provider
            response_message: Response message from provider
            metadata: Additional metadata
            webhook_response: Webhook response data
            request: HttpRequest object for IP and user agent
            
        Returns:
            BillingTransaction object or None if logging failed
        """
        instance = cls()
        return instance._log_transaction(
            transaction_type=transaction_type,
            corporate_id=corporate_id,
            corporate_name=corporate_name,
            user_id=user_id,
            user_email=user_email,
            payment_id=payment_id,
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            message=message,
            state_name=state_name,
            provider=provider,
            provider_reference=provider_reference,
            response_code=response_code,
            response_message=response_message,
            metadata=metadata,
            webhook_response=webhook_response,
            request=request,
        )

    def _log_transaction(
        self,
        transaction_type: str,
        corporate_id: Optional[str] = None,
        corporate_name: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        payment_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: str = "KES",
        message: str = "",
        state_name: str = "Active",
        provider: Optional[str] = None,
        provider_reference: Optional[str] = None,
        response_code: Optional[str] = None,
        response_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        webhook_response: Optional[str] = None,
        request: Optional[HttpRequest] = None,
    ) -> Optional[BillingTransaction]:
        """Internal method that creates the transaction entry"""
        try:
            with transaction.atomic():
                # Get or create State
                state = self._get_state(state_name)

                # Get or create TransactionType
                txn_type = self._get_transaction_type(transaction_type)

                # Extract request context
                source_ip = self._get_request_ip(request)
                user_agent = self._get_user_agent(request)

                # Prepare metadata
                meta_payload = metadata or {}
                if request:
                    meta_payload.update({
                        "user_agent": user_agent,
                        "path": request.path if hasattr(request, 'path') else None,
                        "method": request.method if hasattr(request, 'method') else None,
                    })

                # Create transaction record
                txn_data = {
                    "reference": str(uuid.uuid4()),
                    "transaction_type": txn_type,
                    "corporate_id": corporate_id,
                    "corporate_name": corporate_name or "",
                    "user_id": user_id,
                    "user_email": user_email or "",
                    "payment_id": payment_id,
                    "invoice_id": invoice_id,
                    "subscription_id": subscription_id,
                    "amount": amount or Decimal("0.00"),
                    "currency": currency,
                    "state": state,
                    "message": message,
                    "response_code": response_code or ("200" if state_name == "Completed" else "400"),
                    "response_message": response_message or "",
                    "source_ip": source_ip or "0.0.0.0",
                    "user_agent": user_agent or "",
                    "provider": provider or "",
                    "provider_reference": provider_reference or "",
                    "metadata": meta_payload,
                    "webhook_response": webhook_response or "",
                }

                transaction_obj = BillingTransaction.objects.create(**txn_data)

                logger.info(
                    f"[BillingTransaction] {transaction_type} | "
                    f"corporate={corporate_id} | "
                    f"state={state_name} | "
                    f"ref={transaction_obj.reference}"
                )

                return transaction_obj

        except Exception as e:
            logger.exception(
                f"[BillingTransaction] Failed logging {transaction_type}: {e}"
            )
            return None

    @classmethod
    def log_audit(
        cls,
        action_type: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        corporate_id: Optional[str] = None,
        action_description: str = "",
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        request: Optional[HttpRequest] = None,
    ) -> Optional[AuditLog]:
        """
        Log an audit entry for administrative actions
        
        Args:
            action_type: Type of action (create, update, delete, access, etc.)
            entity_type: Type of entity (payment, invoice, subscription, etc.)
            entity_id: Entity UUID
            user_id: User performing the action
            user_email: User email
            corporate_id: Corporate context
            action_description: Description of the action
            old_values: Previous values (for updates)
            new_values: New values (for updates)
            metadata: Additional metadata
            request: HttpRequest object
            
        Returns:
            AuditLog object or None if logging failed
        """
        instance = cls()
        return instance._log_audit(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            user_email=user_email,
            corporate_id=corporate_id,
            action_description=action_description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            request=request,
        )

    def _log_audit(
        self,
        action_type: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        corporate_id: Optional[str] = None,
        action_description: str = "",
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        request: Optional[HttpRequest] = None,
    ) -> Optional[AuditLog]:
        """Internal method that creates the audit entry"""
        try:
            with transaction.atomic():
                source_ip = self._get_request_ip(request)
                user_agent = self._get_user_agent(request)

                audit_data = {
                    "action_type": action_type,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "user_id": user_id,
                    "user_email": user_email or "",
                    "corporate_id": corporate_id,
                    "action_description": action_description,
                    "old_values": old_values or {},
                    "new_values": new_values or {},
                    "source_ip": source_ip or "0.0.0.0",
                    "user_agent": user_agent or "",
                    "metadata": metadata or {},
                }

                audit_obj = AuditLog.objects.create(**audit_data)

                logger.info(
                    f"[AuditLog] {action_type} | "
                    f"entity={entity_type}:{entity_id} | "
                    f"user={user_email}"
                )

                return audit_obj

        except Exception as e:
            logger.exception(
                f"[AuditLog] Failed logging {action_type} for {entity_type}: {e}"
            )
            return None

    def _get_state(self, state_name: str) -> State:
        """Fetch or create State"""
        return State.objects.get_or_create(
            name=state_name,
            defaults={"description": f"{state_name} state"}
        )[0]

    def _get_transaction_type(self, txn_name: str) -> TransactionType:
        """Fetch or create TransactionType"""
        return TransactionType.objects.get_or_create(
            name=txn_name,
            defaults={
                "simple_name": txn_name,
                "category": "general",
                "description": f"{txn_name} transaction"
            }
        )[0]

    def _get_request_ip(self, request: Optional[HttpRequest]) -> Optional[str]:
        """Extract client IP from request"""
        if not request:
            return None
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def _get_user_agent(self, request: Optional[HttpRequest]) -> Optional[str]:
        """Extract user agent from request"""
        if not request:
            return None
        return request.META.get("HTTP_USER_AGENT", "")


# Convenience alias
TransactionLogBase = TransactionLogger
