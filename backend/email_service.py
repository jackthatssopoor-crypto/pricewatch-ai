"""
PriceWatch AI - Email Automation Service
Powered by SendGrid
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# SendGrid API key (will be set via environment variable)
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@pricewatch-ai.com")
FROM_NAME = "PriceWatch AI"


class EmailService:
    """Handle all email communications"""

    def __init__(self):
        self.sg = SendGridAPIClient(SENDGRID_API_KEY) if SENDGRID_API_KEY else None

    def send_email(self, to_email: str, subject: str, html_content: str, plain_content: str = None) -> bool:
        """
        Send a single email via SendGrid

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_content: Plain text fallback (optional)

        Returns:
            bool: True if sent successfully
        """
        if not self.sg:
            logger.warning("SendGrid not configured, logging email instead")
            logger.info(f"EMAIL TO: {to_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info(f"BODY: {html_content[:200]}...")
            return True

        try:
            message = Mail(
                from_email=Email(FROM_EMAIL, FROM_NAME),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if plain_content:
                message.plain_text_content = Content("text/plain", plain_content)

            response = self.sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                logger.error(f"❌ Email failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ SendGrid error: {str(e)}")
            return False

    # ========================================
    # WELCOME & ONBOARDING EMAILS
    # ========================================

    def send_welcome_email(self, user_email: str, user_name: str = None):
        """Send welcome email after signup"""

        subject = "Welcome to PriceWatch AI! 🚀"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .cta-button {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to PriceWatch AI!</h1>
                    <p>Your competitive intelligence starts now</p>
                </div>
                <div class="content">
                    <p>Hi{f' {user_name}' if user_name else ''},</p>

                    <p>Thank you for joining PriceWatch AI! We're excited to help you stay ahead of the competition.</p>

                    <h3>🚀 Get Started in 3 Steps:</h3>
                    <ol>
                        <li><strong>Add your first product</strong> - Paste a competitor's product URL</li>
                        <li><strong>Set up alerts</strong> - Get notified when prices change</li>
                        <li><strong>Track trends</strong> - Watch your dashboard for insights</li>
                    </ol>

                    <a href="https://app.pricewatch-ai.com/dashboard" class="cta-button">Go to Dashboard</a>

                    <h3>📊 What's Included:</h3>
                    <ul>
                        <li>✅ Automated daily price checks</li>
                        <li>✅ Real-time email alerts</li>
                        <li>✅ Historical price charts</li>
                        <li>✅ Weekly intelligence reports</li>
                    </ul>

                    <p><strong>Need help?</strong> Reply to this email or check out our <a href="https://pricewatch-ai.com/docs">documentation</a>.</p>

                    <p>Happy tracking!</p>
                    <p><strong>The PriceWatch AI Team</strong></p>
                </div>
                <div class="footer">
                    <p>PriceWatch AI | Automated E-commerce Intelligence</p>
                    <p><a href="https://pricewatch-ai.com/unsubscribe">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    # ========================================
    # PRICE ALERT EMAILS
    # ========================================

    def send_price_drop_alert(self, user_email: str, product_name: str, product_url: str,
                              old_price: float, new_price: float, percent_change: float):
        """Send alert when competitor price drops"""

        subject = f"🔥 Price Drop Alert: {product_name} is now ${new_price:.2f}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert-box {{ background: #fff3cd; border-left: 5px solid #ffc107; padding: 20px; margin: 20px 0; }}
                .price-old {{ text-decoration: line-through; color: #888; }}
                .price-new {{ color: #28a745; font-size: 24px; font-weight: bold; }}
                .savings {{ background: #28a745; color: white; padding: 10px; border-radius: 5px; display: inline-block; margin: 10px 0; }}
                .cta-button {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔥 Price Drop Alert!</h2>

                <div class="alert-box">
                    <h3>{product_name}</h3>
                    <p>
                        <span class="price-old">${old_price:.2f}</span> →
                        <span class="price-new">${new_price:.2f}</span>
                    </p>
                    <div class="savings">
                        Save {percent_change:.1f}% (${old_price - new_price:.2f})
                    </div>
                </div>

                <p><strong>What should you do?</strong></p>
                <ul>
                    <li>Consider matching or beating this price</li>
                    <li>Review your profit margins</li>
                    <li>Check if this is a temporary promotion</li>
                </ul>

                <a href="{product_url}" class="cta-button">View Product</a>

                <p style="color: #888; font-size: 12px;">
                    This alert was triggered because you're tracking this product. <a href="https://app.pricewatch-ai.com/alerts">Manage alerts</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    def send_price_increase_alert(self, user_email: str, product_name: str, product_url: str,
                                  old_price: float, new_price: float, percent_change: float):
        """Send alert when competitor price increases"""

        subject = f"📈 Price Increase: {product_name} now ${new_price:.2f}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .alert-box {{ background: #d1ecf1; border-left: 5px solid #17a2b8; padding: 20px; margin: 20px 0; }}
                .price-old {{ color: #888; }}
                .price-new {{ color: #dc3545; font-size: 24px; font-weight: bold; }}
                .opportunity {{ background: #17a2b8; color: white; padding: 10px; border-radius: 5px; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📈 Competitor Price Increased!</h2>

                <div class="alert-box">
                    <h3>{product_name}</h3>
                    <p>
                        <span class="price-old">${old_price:.2f}</span> →
                        <span class="price-new">${new_price:.2f}</span>
                    </p>
                    <div class="opportunity">
                        Opportunity: {percent_change:.1f}% increase
                    </div>
                </div>

                <p><strong>This could be your chance to:</strong></p>
                <ul>
                    <li>Maintain your current price and gain competitive advantage</li>
                    <li>Slightly increase your price while staying competitive</li>
                    <li>Capture more market share at your current pricing</li>
                </ul>

                <p style="color: #888; font-size: 12px;">
                    <a href="https://app.pricewatch-ai.com/alerts">Manage alerts</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    # ========================================
    # WEEKLY REPORT EMAIL
    # ========================================

    def send_weekly_report(self, user_email: str, report_data: Dict[str, Any]):
        """Send weekly price intelligence report"""

        subject = f"📊 Your Weekly Price Intelligence Report - {datetime.now().strftime('%b %d, %Y')}"

        products_tracked = report_data.get("products_tracked", 0)
        price_changes = report_data.get("price_changes", 0)
        avg_competitor_price = report_data.get("avg_competitor_price", 0)
        top_opportunities = report_data.get("top_opportunities", [])

        opportunities_html = ""
        for opp in top_opportunities[:5]:
            opportunities_html += f"""
            <li>
                <strong>{opp['name']}</strong><br>
                Price dropped {opp['percent_drop']:.1f}% to ${opp['new_price']:.2f}
            </li>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
                .stat-number {{ font-size: 32px; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📊 Your Weekly Price Intelligence Report</h2>
                <p style="color: #888;">{datetime.now().strftime('%B %d, %Y')}</p>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{products_tracked}</div>
                        <div class="stat-label">Products Tracked</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{price_changes}</div>
                        <div class="stat-label">Price Changes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${avg_competitor_price:.2f}</div>
                        <div class="stat-label">Avg. Price</div>
                    </div>
                </div>

                <h3>🎯 Top Opportunities This Week</h3>
                <ul>
                    {opportunities_html or '<li>No significant price changes this week</li>'}
                </ul>

                <a href="https://app.pricewatch-ai.com/dashboard" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
                    View Full Report
                </a>

                <p style="color: #888; font-size: 12px;">
                    Sent every Monday | <a href="https://app.pricewatch-ai.com/settings">Manage preferences</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    # ========================================
    # BILLING & SUBSCRIPTION EMAILS
    # ========================================

    def send_payment_failed_email(self, user_email: str, amount: float, retry_date: str):
        """Send notification when payment fails"""

        subject = "Payment Failed - Action Required"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .warning-box {{ background: #f8d7da; border-left: 5px solid #dc3545; padding: 20px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>⚠️ Payment Failed</h2>

                <div class="warning-box">
                    <p><strong>We couldn't process your payment of ${amount:.2f}</strong></p>
                    <p>Your subscription will remain active until {retry_date}, after which it will be paused.</p>
                </div>

                <p><strong>What to do:</strong></p>
                <ol>
                    <li>Update your payment method in your account settings</li>
                    <li>Ensure you have sufficient funds</li>
                    <li>Contact your bank if issues persist</li>
                </ol>

                <a href="https://app.pricewatch-ai.com/billing" style="background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
                    Update Payment Method
                </a>

                <p>Need help? Reply to this email and we'll assist you.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    def send_subscription_cancelled_email(self, user_email: str):
        """Send confirmation when user cancels subscription"""

        subject = "Subscription Cancelled - We're Sorry to See You Go"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Subscription Cancelled</h2>

                <p>Your subscription has been cancelled. You'll continue to have access until the end of your billing period.</p>

                <p><strong>We'd love your feedback:</strong></p>
                <p>What made you decide to cancel? Your input helps us improve.</p>

                <a href="https://pricewatch-ai.com/feedback" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
                    Share Feedback
                </a>

                <p>You can always re-activate your account anytime.</p>

                <p>Thanks for using PriceWatch AI!</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)

    # ========================================
    # RE-ENGAGEMENT EMAILS
    # ========================================

    def send_inactive_user_email(self, user_email: str, days_inactive: int):
        """Send re-engagement email to inactive users"""

        subject = f"We Miss You! Come Back to PriceWatch AI"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>👋 We Miss You!</h2>

                <p>It's been {days_inactive} days since you last checked your PriceWatch AI dashboard.</p>

                <p><strong>Here's what you might be missing:</strong></p>
                <ul>
                    <li>Competitor price changes in your market</li>
                    <li>Opportunities to optimize your pricing</li>
                    <li>Insights that could increase your profit margins</li>
                </ul>

                <a href="https://app.pricewatch-ai.com/dashboard" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
                    Check Your Dashboard
                </a>

                <p>Need help getting started? We're here to assist!</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(user_email, subject, html_content)


# Singleton instance
email_service = EmailService()
