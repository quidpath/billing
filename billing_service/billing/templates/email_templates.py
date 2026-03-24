"""
Centralized email templates for Billing Service
All email HTML should be defined here to maintain consistency
"""
from datetime import datetime


class BillingEmailTemplates:
    """Email templates for billing notifications"""
    
    @staticmethod
    def replace_tags(template_string, **kwargs):
        """Replace all occurrences of [tag_name] with provided values"""
        try:
            for key, value in kwargs.items():
                template_string = template_string.replace(f"[{key}]", str(value))
            return template_string
        except Exception as e:
            print(f"replace_tags Exception: {e}")
            return template_string

    @staticmethod
    def get_base_style():
        """Common CSS styles for all billing emails"""
        return """
        <style>
            body {
                font-family: Arial, sans-serif;
                color: #333;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #ffffff;
            }
            .header {
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }
            .content {
                padding: 30px 20px;
            }
            .info-box {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .info-box h3 {
                margin-top: 0;
                color: #2c3e50;
            }
            .info-box p {
                margin: 8px 0;
            }
            .cta-button {
                display: inline-block;
                background-color: #3498db;
                color: white !important;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 5px;
                margin: 30px 0;
            }
            .success-banner {
                background-color: #d4edda;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #28a745;
            }
            .success-banner h2 {
                color: #155724;
                margin: 0;
            }
            .warning-banner {
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #f39c12;
            }
            .warning-banner h2 {
                color: #856404;
                margin: 0;
            }
            .footer {
                border-top: 1px solid #ecf0f1;
                margin-top: 30px;
                padding-top: 20px;
                color: #95a5a6;
                font-size: 12px;
                text-align: center;
            }
        </style>
        """

    @classmethod
    def invoice_created(cls, **kwargs):
        """Template for new invoice notification"""
        template = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            [base_style]
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">New Invoice from Quidpath</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>[corporate_name]</strong>,</p>
                    <p>A new invoice has been generated for your Quidpath subscription.</p>
                    
                    <div class="info-box">
                        <h3>Invoice Details</h3>
                        <p><strong>Invoice Number:</strong> [invoice_number]</p>
                        <p><strong>Amount:</strong> [currency] [total_amount]</p>
                        <p><strong>Due Date:</strong> [due_date]</p>
                        <p><strong>Billing Period:</strong> [billing_period]</p>
                    </div>
                    
                    <p>Please log in to your Quidpath account to view the full invoice and make payment.</p>
                    
                    <div style="text-align: center;">
                        <a href="[invoice_url]" class="cta-button">View Invoice</a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 14px;">
                        If you have any questions about this invoice, please contact our support team.
                    </p>
                </div>
                <div class="footer">
                    This is an automated message from Quidpath Billing System.<br>
                    © [year] Quidpath. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        return cls.replace_tags(template, base_style=cls.get_base_style(), year=datetime.now().year, **kwargs)

    @classmethod
    def payment_confirmed(cls, **kwargs):
        """Template for payment confirmation"""
        template = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            [base_style]
        </head>
        <body>
            <div class="container">
                <div class="success-banner">
                    <h2>Payment Confirmed!</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>[corporate_name]</strong>,</p>
                    <p>We have successfully received your payment. Thank you!</p>
                    
                    <div class="info-box">
                        <h3>Payment Details</h3>
                        <p><strong>Transaction ID:</strong> [transaction_id]</p>
                        <p><strong>Invoice Number:</strong> [invoice_number]</p>
                        <p><strong>Amount Paid:</strong> [currency] [amount]</p>
                        <p><strong>Payment Method:</strong> [payment_method]</p>
                        <p><strong>Payment Date:</strong> [payment_date]</p>
                    </div>
                    
                    <p>Your subscription is now active and you can continue using Quidpath without interruption.</p>
                    
                    <div style="text-align: center;">
                        <a href="[receipt_url]" class="cta-button" style="background-color: #28a745;">View Receipt</a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Thank you for being a valued Quidpath customer!
                    </p>
                </div>
                <div class="footer">
                    This is an automated message from Quidpath Billing System.<br>
                    © [year] Quidpath. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        return cls.replace_tags(template, base_style=cls.get_base_style(), year=datetime.now().year, **kwargs)

    @classmethod
    def invoice_reminder(cls, **kwargs):
        """Template for invoice payment reminder"""
        template = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            [base_style]
        </head>
        <body>
            <div class="container">
                <div class="warning-banner">
                    <h2>Payment Reminder</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>[corporate_name]</strong>,</p>
                    <p>This is a friendly reminder that your invoice payment is due [urgency_message].</p>
                    
                    <div class="info-box">
                        <h3>Invoice Details</h3>
                        <p><strong>Invoice Number:</strong> [invoice_number]</p>
                        <p><strong>Amount Due:</strong> [currency] [total_amount]</p>
                        <p><strong>Due Date:</strong> <span style="color: [urgency_color]; font-weight: bold;">[due_date]</span></p>
                        <p><strong>Days Remaining:</strong> [days_until_due] days</p>
                    </div>
                    
                    <p>To avoid any interruption to your Quidpath service, please make payment before the due date.</p>
                    
                    <div style="text-align: center;">
                        <a href="[payment_url]" class="cta-button" style="background-color: [urgency_color];">Pay Now</a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 14px;">
                        If you have already made payment, please disregard this reminder.
                    </p>
                </div>
                <div class="footer">
                    This is an automated message from Quidpath Billing System.<br>
                    © [year] Quidpath. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        return cls.replace_tags(template, base_style=cls.get_base_style(), year=datetime.now().year, **kwargs)

    @classmethod
    def trial_expiring(cls, **kwargs):
        """Template for trial expiration notification"""
        template = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            [base_style]
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">Your Trial is Ending Soon</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>[corporate_name]</strong>,</p>
                    <p>Your free trial of Quidpath will expire in <strong>[days_remaining] days</strong>.</p>
                    
                    <div class="info-box">
                        <h3>Trial Information</h3>
                        <p><strong>Trial End Date:</strong> [end_date]</p>
                        <p><strong>Days Remaining:</strong> [days_remaining] days</p>
                    </div>
                    
                    <p>To continue enjoying Quidpath's powerful ERP features, please subscribe to one of our plans.</p>
                    
                    <div style="text-align: center;">
                        <a href="[plans_url]" class="cta-button">View Plans & Subscribe</a>
                    </div>
                    
                    <p style="color: #7f8c8d; font-size: 14px;">
                        Don't lose access to your data and workflows. Subscribe today!
                    </p>
                </div>
                <div class="footer">
                    This is an automated message from Quidpath Billing System.<br>
                    © [year] Quidpath. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """
        return cls.replace_tags(template, base_style=cls.get_base_style(), year=datetime.now().year, **kwargs)
