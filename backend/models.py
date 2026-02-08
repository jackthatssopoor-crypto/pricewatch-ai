"""
PriceWatch AI - Database Models (SQLAlchemy)
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class PlanTier(str, enum.Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AlertType(str, enum.Enum):
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    THRESHOLD = "threshold"
    STOCK_CHANGE = "stock_change"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    plan = Column(Enum(PlanTier), default=PlanTier.STARTER)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, default="Default Key")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="api_keys")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    name = Column(String, nullable=True)
    competitor_name = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    last_checked = Column(DateTime, nullable=True)
    check_interval = Column(Integer, default=86400)  # Seconds (default: daily)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Stock tracking
    in_stock = Column(Boolean, nullable=True)
    last_in_stock = Column(DateTime, nullable=True)

    # Metadata
    domain = Column(String, nullable=True, index=True)
    product_identifier = Column(String, nullable=True)  # ASIN, SKU, etc.

    # Relationships
    user = relationship("User", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    in_stock = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Scraping metadata
    source = Column(String, default="scraper")
    scrape_duration = Column(Float, nullable=True)  # Seconds
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="price_history")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    alert_type = Column(Enum(AlertType), nullable=False)
    threshold = Column(Float, nullable=True)  # For threshold-based alerts
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="alerts")
    product = relationship("Product", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False, index=True)
    notification_type = Column(String, default="email")  # email, webhook, sms
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered = Column(Boolean, default=False)
    delivery_attempts = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)

    # Email-specific
    email_to = Column(String, nullable=True)
    email_subject = Column(String, nullable=True)

    # Webhook-specific
    webhook_url = Column(Text, nullable=True)
    webhook_response_code = Column(Integer, nullable=True)

    # Relationships
    alert = relationship("Alert", back_populates="notifications")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    events = Column(Text, nullable=False)  # JSON array of event types
    secret = Column(String, nullable=True)  # For signature verification
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="webhooks")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String, default="weekly")  # weekly, monthly, custom
    generated_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    file_path = Column(Text, nullable=True)  # S3 or local path to PDF
    email_sent = Column(Boolean, default=False)
    products_count = Column(Integer, default=0)
    price_changes_count = Column(Integer, default=0)

    # Summary statistics
    avg_price = Column(Float, nullable=True)
    lowest_price = Column(Float, nullable=True)
    highest_price = Column(Float, nullable=True)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    log_level = Column(String, default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String, nullable=False)  # scraper, api, celery, etc.
    message = Column(Text, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    product_id = Column(String, nullable=True, index=True)
    error_trace = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON additional data
