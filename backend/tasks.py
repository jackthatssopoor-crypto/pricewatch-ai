"""
PriceWatch AI - Celery Background Tasks
Automated price checking and alert processing
"""

from celery import Celery
from celery.schedules import crontab
import asyncio
from datetime import datetime, timedelta
from typing import List
import logging

# Initialize Celery
celery_app = Celery(
    "pricewatch",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = logging.getLogger(__name__)


# ========================================
# PERIODIC TASKS SCHEDULE
# ========================================

celery_app.conf.beat_schedule = {
    # Check prices every 15 minutes for Business tier
    "check-business-tier-prices": {
        "task": "tasks.check_products_by_tier",
        "schedule": crontab(minute="*/15"),
        "args": ("business",)
    },
    # Check prices hourly for Professional tier
    "check-professional-tier-prices": {
        "task": "tasks.check_products_by_tier",
        "schedule": crontab(minute=0),
        "args": ("professional",)
    },
    # Check prices daily for Starter tier
    "check-starter-tier-prices": {
        "task": "tasks.check_products_by_tier",
        "schedule": crontab(hour=9, minute=0),  # 9 AM UTC
        "args": ("starter",)
    },
    # Generate weekly reports
    "generate-weekly-reports": {
        "task": "tasks.generate_all_weekly_reports",
        "schedule": crontab(day_of_week=1, hour=10, minute=0),  # Monday 10 AM
    },
    # Clean up old price history (keep 90 days)
    "cleanup-old-data": {
        "task": "tasks.cleanup_old_price_history",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),  # 1st of month, 2 AM
    },
    # Monitor failed payments and send dunning emails
    "process-failed-payments": {
        "task": "tasks.process_failed_payments",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    # Check for inactive users and send re-engagement emails
    "reactivate-inactive-users": {
        "task": "tasks.reactivate_inactive_users",
        "schedule": crontab(day_of_week=3, hour=14, minute=0),  # Wednesday 2 PM
    },
}


# ========================================
# PRICE CHECKING TASKS
# ========================================

@celery_app.task(name="tasks.check_single_product")
def check_single_product(product_id: str):
    """
    Check price for a single product
    This is the core task that gets called repeatedly
    """
    from scraper import PriceScraper
    # from database import get_product, save_price_history, update_product_price
    # from alerts import check_and_trigger_alerts

    logger.info(f"Checking price for product: {product_id}")

    try:
        # Get product from database
        # product = get_product(product_id)
        # For now, mock data
        product = {
            "id": product_id,
            "url": "https://www.amazon.com/dp/B0BSHF7WHW",
            "user_id": "user_123"
        }

        # Scrape price
        scraper = PriceScraper()
        result = asyncio.run(scraper.scrape_product(product["url"]))
        asyncio.run(scraper.close())

        if result["success"]:
            # Save to database
            # save_price_history(product_id, result)
            # update_product_price(product_id, result["price"])

            # Check if alerts should be triggered
            # check_and_trigger_alerts(product_id, result["price"])

            logger.info(f"✅ Price updated for {product_id}: ${result['price']}")
            return {
                "success": True,
                "product_id": product_id,
                "price": result["price"],
                "name": result["name"]
            }
        else:
            logger.error(f"❌ Failed to scrape {product_id}: {result.get('error')}")
            return {"success": False, "product_id": product_id, "error": result.get("error")}

    except Exception as e:
        logger.error(f"❌ Error checking product {product_id}: {str(e)}")
        return {"success": False, "product_id": product_id, "error": str(e)}


@celery_app.task(name="tasks.check_products_by_tier")
def check_products_by_tier(tier: str):
    """
    Check all products for users in a specific pricing tier
    Called by periodic schedule
    """
    logger.info(f"Checking products for tier: {tier}")

    # from database import get_products_by_tier

    # Mock: get product IDs
    # product_ids = get_products_by_tier(tier)
    product_ids = []  # Will be populated from database

    # Queue individual tasks
    for product_id in product_ids:
        check_single_product.delay(product_id)

    logger.info(f"Queued {len(product_ids)} products for tier {tier}")
    return {"tier": tier, "products_queued": len(product_ids)}


@celery_app.task(name="tasks.check_multiple_products")
def check_multiple_products(product_ids: List[str]):
    """
    Check multiple products in parallel
    Useful for bulk operations
    """
    from celery import group

    job = group(check_single_product.s(pid) for pid in product_ids)
    results = job.apply_async()

    return {"total": len(product_ids), "task_id": results.id}


# ========================================
# ALERT TASKS
# ========================================

@celery_app.task(name="tasks.send_price_alert_email")
def send_price_alert_email(user_email: str, product_name: str, old_price: float, new_price: float, alert_type: str):
    """Send price alert email to user"""
    # from email_service import send_alert_email

    logger.info(f"Sending alert to {user_email} for {product_name}")

    try:
        # Mock email sending
        # send_alert_email(user_email, {
        #     "product_name": product_name,
        #     "old_price": old_price,
        #     "new_price": new_price,
        #     "alert_type": alert_type
        # })

        logger.info(f"✅ Alert email sent to {user_email}")
        return {"success": True, "email": user_email}

    except Exception as e:
        logger.error(f"❌ Failed to send email to {user_email}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="tasks.trigger_webhook")
def trigger_webhook(webhook_url: str, payload: dict):
    """Trigger webhook for price alert (Premium feature)"""
    import httpx

    logger.info(f"Triggering webhook: {webhook_url}")

    try:
        response = httpx.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        logger.info(f"✅ Webhook delivered: {response.status_code}")
        return {"success": True, "status_code": response.status_code}

    except Exception as e:
        logger.error(f"❌ Webhook failed: {str(e)}")
        return {"success": False, "error": str(e)}


# ========================================
# REPORT GENERATION TASKS
# ========================================

@celery_app.task(name="tasks.generate_weekly_report")
def generate_weekly_report(user_id: str):
    """Generate weekly price intelligence report for user"""
    # from report_generator import create_pdf_report
    # from email_service import send_report_email
    # from database import get_user_products, get_price_changes_last_week

    logger.info(f"Generating weekly report for user: {user_id}")

    try:
        # Mock report generation
        # products = get_user_products(user_id)
        # price_changes = get_price_changes_last_week(user_id)
        # pdf_path = create_pdf_report(user_id, products, price_changes)
        # send_report_email(user_id, pdf_path)

        logger.info(f"✅ Weekly report generated for {user_id}")
        return {"success": True, "user_id": user_id}

    except Exception as e:
        logger.error(f"❌ Report generation failed for {user_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="tasks.generate_all_weekly_reports")
def generate_all_weekly_reports():
    """Generate weekly reports for all active users"""
    # from database import get_all_active_users

    logger.info("Generating weekly reports for all users")

    # Mock: get all user IDs
    # user_ids = get_all_active_users()
    user_ids = []  # Will be populated from database

    # Queue individual report generation tasks
    for user_id in user_ids:
        generate_weekly_report.delay(user_id)

    logger.info(f"Queued {len(user_ids)} weekly reports")
    return {"reports_queued": len(user_ids)}


# ========================================
# MAINTENANCE TASKS
# ========================================

@celery_app.task(name="tasks.cleanup_old_price_history")
def cleanup_old_price_history(days_to_keep: int = 90):
    """Delete price history older than X days to save storage"""
    # from database import delete_old_price_history

    logger.info(f"Cleaning up price history older than {days_to_keep} days")

    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        # deleted_count = delete_old_price_history(cutoff_date)

        deleted_count = 0  # Mock
        logger.info(f"✅ Deleted {deleted_count} old price records")
        return {"success": True, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="tasks.process_failed_payments")
def process_failed_payments():
    """Handle failed Stripe payments - send dunning emails"""
    # from database import get_failed_payments
    # from email_service import send_payment_failed_email

    logger.info("Processing failed payments")

    try:
        # failed_payments = get_failed_payments()
        failed_payments = []  # Mock

        for payment in failed_payments:
            # send_payment_failed_email(payment["user_id"], payment["amount"])
            pass

        logger.info(f"✅ Processed {len(failed_payments)} failed payments")
        return {"success": True, "count": len(failed_payments)}

    except Exception as e:
        logger.error(f"❌ Failed payment processing error: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="tasks.reactivate_inactive_users")
def reactivate_inactive_users():
    """Send re-engagement emails to users who haven't logged in for 7+ days"""
    # from database import get_inactive_users
    # from email_service import send_reactivation_email

    logger.info("Checking for inactive users")

    try:
        # inactive_users = get_inactive_users(days_inactive=7)
        inactive_users = []  # Mock

        for user in inactive_users:
            # send_reactivation_email(user["email"], user["id"])
            pass

        logger.info(f"✅ Sent {len(inactive_users)} reactivation emails")
        return {"success": True, "count": len(inactive_users)}

    except Exception as e:
        logger.error(f"❌ Reactivation task error: {str(e)}")
        return {"success": False, "error": str(e)}


# ========================================
# UTILITY TASKS
# ========================================

@celery_app.task(name="tasks.health_check")
def health_check():
    """Simple health check task to verify Celery is working"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "PriceWatch AI - Celery"
    }


@celery_app.task(name="tasks.test_scraper")
def test_scraper(url: str):
    """Test scraping a single URL (for debugging)"""
    from scraper import PriceScraper

    scraper = PriceScraper()
    result = asyncio.run(scraper.scrape_product(url))
    asyncio.run(scraper.close())

    return result


if __name__ == "__main__":
    # Start worker: celery -A tasks worker --loglevel=info
    # Start beat: celery -A tasks beat --loglevel=info
    print("PriceWatch AI - Celery Tasks Loaded")
    print("Run with: celery -A tasks worker --loglevel=info")
