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

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">New Invoice from Quidpath</h2>
                <p>Dear {invoice.corporate_name},</p>
                <p>A new invoice has been generated for your Quidpath subscription.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Invoice Details</h3>
                    <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                    <p><strong>Amount:</strong> {invoice.currency} {invoice.total_amount}</p>
                    <p><strong>Due Date:</strong> {invoice.due_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Billing Period:</strong> {invoice.billing_period_start.strftime('%B %d, %Y')} - {invoice.billing_period_end.strftime('%B %d, %Y')}</p>
                </div>
                
                <p>Please log in to your Quidpath account to view the full invoice and make payment.</p>
                
                <div style="margin: 30px 0;">
                    <a href="https://app.quidpath.com/billing/invoices" 
                       style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Invoice
                    </a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 14px;">
                    If you have any questions about this invoice, please contact our support team.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    This is an automated message from Quidpath Billing System.<br>
                    © {datetime.now().year} Quidpath. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

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

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                    <h2 style="color: #155724; margin: 0;">Payment Confirmed!</h2>
                </div>
                
                <p>Dear {payment.invoice.corporate_name},</p>
                <p>We have successfully received your payment. Thank you!</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Payment Details</h3>
                    <p><strong>Transaction ID:</strong> {payment.transaction_id or payment.id}</p>
                    <p><strong>Invoice Number:</strong> {payment.invoice.invoice_number}</p>
                    <p><strong>Amount Paid:</strong> {payment.currency} {payment.amount}</p>
                    <p><strong>Payment Method:</strong> {payment.payment_method.upper()}</p>
                    <p><strong>Payment Date:</strong> {payment.paid_at.strftime('%B %d, %Y %I:%M %p') if payment.paid_at else 'N/A'}</p>
                </div>
                
                <p>Your subscription is now active and you can continue using Quidpath without interruption.</p>
                
                <div style="margin: 30px 0;">
                    <a href="https://app.quidpath.com/billing/invoices" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Receipt
                    </a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 14px;">
                    Thank you for being a valued Quidpath customer!
                </p>
                
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    This is an automated message from Quidpath Billing System.<br>
                    © {datetime.now().year} Quidpath. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

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

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid {urgency_color};">
                    <h2 style="color: #856404; margin: 0;">Payment Reminder</h2>
                </div>
                
                <p>Dear {invoice.corporate_name},</p>
                <p>This is a friendly reminder that your invoice payment is due {urgency_message}.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Invoice Details</h3>
                    <p><strong>Invoice Number:</strong> {invoice.invoice_number}</p>
                    <p><strong>Amount Due:</strong> {invoice.currency} {invoice.total_amount}</p>
                    <p><strong>Due Date:</strong> <span style="color: {urgency_color}; font-weight: bold;">{invoice.due_date.strftime('%B %d, %Y')}</span></p>
                    <p><strong>Days Remaining:</strong> {days_until_due} days</p>
                </div>
                
                <p>To avoid any interruption to your Quidpath service, please make payment before the due date.</p>
                
                <div style="margin: 30px 0;">
                    <a href="https://app.quidpath.com/billing/invoices/{invoice.id}" 
                       style="background-color: {urgency_color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Pay Now
                    </a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 14px;">
                    If you have already made payment, please disregard this reminder.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    This is an automated message from Quidpath Billing System.<br>
                    © {datetime.now().year} Quidpath. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

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

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Your Trial is Ending Soon</h2>
                <p>Dear {trial.corporate_name},</p>
                <p>Your free trial of Quidpath will expire in <strong>{days_remaining} days</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Trial Information</h3>
                    <p><strong>Trial End Date:</strong> {trial.end_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Days Remaining:</strong> {days_remaining} days</p>
                </div>
                
                <p>To continue enjoying Quidpath's powerful ERP features, please subscribe to one of our plans.</p>
                
                <div style="margin: 30px 0;">
                    <a href="https://app.quidpath.com/billing/plans" 
                       style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Plans & Subscribe
                    </a>
                </div>
                
                <p style="color: #7f8c8d; font-size: 14px;">
                    Don't lose access to your data and workflows. Subscribe today!
                </p>
                
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 30px 0;">
                <p style="color: #95a5a6; font-size: 12px;">
                    This is an automated message from Quidpath Billing System.<br>
                    © {datetime.now().year} Quidpath. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Your Trial is Ending Soon
        
        Dear {trial.corporate_name},
        
        Your free trial of Quidpath will expire in {days_remaining} days.
        
        Trial Information:
        - Trial End Date: {trial.end_date.strftime('%B %d, %Y')}
        - Days Remaining: {days_remaining} days
        
        To continue enjoying Quidpath's powerful ERP features, please subscribe to one of our plans.
        
        Don't lose access to your data and workflows. Subscribe today!
        
        Visit: https://app.quidpath.com/billing/plans
        
        © {datetime.now().year} Quidpath. All rights reserved.
        """

        return NotificationService.send_email(
            corporate_email, subject, html_body, text_body
        )
