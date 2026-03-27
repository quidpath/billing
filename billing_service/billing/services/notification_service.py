"""
Notification Service for Billing
Handles email notifications for invoices, payments, and subscription events
"""

import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from billing_service.billing.templates.email_templates import BillingEmailTemplates

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending billing notifications"""

    @staticmethod
    def send_email(
        to_email: str, subject: str, html_body: str, text_body: Optional[str] = None
    ) -> bool:
        """Send email notification"""
        try:
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", 587))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_pass = os.environ.get("SMTP_PASSWORD", "")
            from_email = os.environ.get("DEFAULT_FROM_EMAIL", "billing@quidpath.com")

            if not smtp_user or not smtp_pass:
                logger.warning("SMTP credentials not configured, skipping email")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            if text_body:
                part1 = MIMEText(text_body, "plain")
                msg.attach(part1)

            part2 = MIMEText(html_body, "html")
            msg.attach(part2)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_invoice_created_notification(invoice, corporate_email: str) -> bool:
        """Send notification when new invoice is created"""
        subject = f"New Invoice {invoice.invoice_number} - Quidpath Billing"

        replace_items = {
            "corporate_name": invoice.corporate_name,
            "invoice_number": invoice.invoice_number,
            "currency": invoice.currency,
            "total_amount": invoice.total_amount,
            "due_date": invoice.due_date.strftime('%B %d, %Y'),
            "billing_period": f"{invoice.billing_period_start.strftime('%B %d, %Y')} - {invoice.billing_period_end.strftime('%B %d, %Y')}",
            "invoice_url": "https://stage.quidpath.com/billing/invoices",
        }
        html_body = BillingEmailTemplates.invoice_created(**replace_items)

        text_body = f"""
        New Invoice from Quidpath
        
        Dear {invoice.corporate_name},
        
        A new invoice has been generated for your Quidpath subscription.
        
        Invoice Details:
        - Invoice Number: {invoice.invoice_number}
        - Amount: {invoice.currency} {invoice.total_amount}
        - Due Date: {invoice.due_date.strftime('%B %d, %Y')}
        - Billing Period: {invoice.billing_period_start.strftime('%B %d, %Y')} - {invoice.billing_period_end.strftime('%B %d, %Y')}
        
        Please log in to your Quidpath account to view the full invoice and make payment.
        
        If you have any questions, please contact our support team.
        
        © {datetime.now().year} Quidpath. All rights reserved.
        """

        return NotificationService.send_email(
            corporate_email, subject, html_body, text_body
        )

    @staticmethod
    def send_payment_confirmation_notification(payment, corporate_email: str) -> bool:
        """Send notification when payment is confirmed"""
        subject = f"Payment Confirmed - Invoice {payment.invoice.invoice_number}"

        replace_items = {
            "corporate_name": payment.invoice.corporate_name,
            "transaction_id": payment.transaction_id or str(payment.id),
            "invoice_number": payment.invoice.invoice_number,
            "currency": payment.currency,
            "amount": payment.amount,
            "payment_method": payment.payment_method.upper(),
            "payment_date": payment.paid_at.strftime('%B %d, %Y %I:%M %p') if payment.paid_at else 'N/A',
            "receipt_url": "https://stage.quidpath.com/billing/invoices",
        }
        html_body = BillingEmailTemplates.payment_confirmed(**replace_items)

        text_body = f"""
        Payment Confirmed!
        
        Dear {payment.invoice.corporate_name},
        
        We have successfully received your payment. Thank you!
        
        Payment Details:
        - Transaction ID: {payment.transaction_id or payment.id}
        - Invoice Number: {payment.invoice.invoice_number}
        - Amount Paid: {payment.currency} {payment.amount}
        - Payment Method: {payment.payment_method.upper()}
        - Payment Date: {payment.paid_at.strftime('%B %d, %Y %I:%M %p') if payment.paid_at else 'N/A'}
        
        Your subscription is now active and you can continue using Quidpath without interruption.
        
        Thank you for being a valued Quidpath customer!
        
        © {datetime.now().year} Quidpath. All rights reserved.
        """

        return NotificationService.send_email(
            corporate_email, subject, html_body, text_body
        )

    @staticmethod
    def send_invoice_reminder_notification(
        invoice, corporate_email: str, days_until_due: int
    ) -> bool:
        """Send reminder notification for upcoming invoice due date"""
        subject = f"Payment Reminder - Invoice {invoice.invoice_number} Due in {days_until_due} Days"

        urgency_color = "#f39c12" if days_until_due > 3 else "#e74c3c"
        urgency_message = "soon" if days_until_due > 3 else "very soon"

        replace_items = {
            "corporate_name": invoice.corporate_name,
            "urgency_message": urgency_message,
            "invoice_number": invoice.invoice_number,
            "currency": invoice.currency,
            "total_amount": invoice.total_amount,
            "due_date": invoice.due_date.strftime('%B %d, %Y'),
            "days_until_due": days_until_due,
            "urgency_color": urgency_color,
            "payment_url": f"https://stage.quidpath.com/billing/invoices/{invoice.id}",
        }
        html_body = BillingEmailTemplates.invoice_reminder(**replace_items)

        text_body = f"""
        Payment Reminder
        
        Dear {invoice.corporate_name},
        
        This is a friendly reminder that your invoice payment is due {urgency_message}.
        
        Invoice Details:
        - Invoice Number: {invoice.invoice_number}
        - Amount Due: {invoice.currency} {invoice.total_amount}
        - Due Date: {invoice.due_date.strftime('%B %d, %Y')}
        - Days Remaining: {days_until_due} days
        
        To avoid any interruption to your Quidpath service, please make payment before the due date.
        
        If you have already made payment, please disregard this reminder.
        
        © {datetime.now().year} Quidpath. All rights reserved.
        """

        return NotificationService.send_email(
            corporate_email, subject, html_body, text_body
        )

    @staticmethod
    def send_trial_expiring_notification(
        trial, corporate_email: str, days_remaining: int
    ) -> bool:
        """Send notification when trial is about to expire"""
        subject = f"Your Quidpath Trial Expires in {days_remaining} Days"

        replace_items = {
            "corporate_name": trial.corporate_name,
            "days_remaining": days_remaining,
            "end_date": trial.end_date.strftime('%B %d, %Y'),
            "plans_url": "https://stage.quidpath.com/billing/plans",
        }
        html_body = BillingEmailTemplates.trial_expiring(**replace_items)

        text_body = f"""
        Your Trial is Ending Soon
        
        Dear {trial.corporate_name},
        
        Your free trial of Quidpath will expire in {days_remaining} days.
        
        Trial Information:
        - Trial End Date: {trial.end_date.strftime('%B %d, %Y')}
        - Days Remaining: {days_remaining} days
        
        To continue enjoying Quidpath's powerful ERP features, please subscribe to one of our plans.
        
        Don't lose access to your data and workflows. Subscribe today!
        
        Visit: https://stage.quidpath.com/billing/plans
        
        © {datetime.now().year} Quidpath. All rights reserved.
        """

        return NotificationService.send_email(
            corporate_email, subject, html_body, text_body
        )
