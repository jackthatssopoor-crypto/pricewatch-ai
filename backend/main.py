"""
PriceWatch AI - Main FastAPI Application
Automated E-commerce Price Intelligence Platform
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import hashlib
import secrets
from enum import Enum

# Initialize FastAPI
app = FastAPI(
    title="PriceWatch AI",
    description="Automated E-commerce Competitive Intelligence Platform",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ========================================
# DATA MODELS
# ========================================

class PlanTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class AlertType(str, Enum):
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase"
    THRESHOLD = "threshold"
    STOCK_CHANGE = "stock_change"

# Request Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    plan: PlanTier = PlanTier.STARTER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProductAdd(BaseModel):
    url: HttpUrl
    name: Optional[str] = None
    competitor_name: Optional[str] = None
    alert_threshold: Optional[float] = None

class AlertConfig(BaseModel):
    product_id: str
    alert_type: AlertType
    threshold: Optional[float] = None
    enabled: bool = True

class WebhookConfig(BaseModel):
    url: HttpUrl
    events: List[str]
    enabled: bool = True

# Response Models
class ProductResponse(BaseModel):
    id: str
    url: str
    name: str
    current_price: Optional[float]
    last_checked: Optional[datetime]
    price_history: List[Dict[str, Any]]
    competitor_name: Optional[str]

class DashboardStats(BaseModel):
    total_products: int
    active_alerts: int
    price_changes_24h: int
    average_competitor_price: Optional[float]
    lowest_price_found: Optional[float]
    highest_price_found: Optional[float]

class UserProfile(BaseModel):
    id: str
    email: str
    plan: PlanTier
    products_tracked: int
    products_limit: int
    created_at: datetime
    subscription_status: str

# ========================================
# IN-MEMORY DATABASE (Will migrate to PostgreSQL)
# ========================================

# Temporary storage - will be replaced with PostgreSQL
USERS_DB = {}
PRODUCTS_DB = {}
PRICES_DB = {}
ALERTS_DB = {}
API_KEYS = {}

# Plan limits
PLAN_LIMITS = {
    PlanTier.STARTER: {"products": 50, "check_interval": 86400},  # Daily
    PlanTier.PROFESSIONAL: {"products": 200, "check_interval": 3600},  # Hourly
    PlanTier.BUSINESS: {"products": 500, "check_interval": 900},  # 15 min
    PlanTier.ENTERPRISE: {"products": -1, "check_interval": 60},  # 1 min (unlimited)
}

# ========================================
# HELPER FUNCTIONS
# ========================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_api_key() -> str:
    """Generate secure API key"""
    return f"pk_{''.join(secrets.token_urlsafe(32))}"

def generate_user_id() -> str:
    """Generate unique user ID"""
    return f"user_{secrets.token_urlsafe(16)}"

def generate_product_id() -> str:
    """Generate unique product ID"""
    return f"prod_{secrets.token_urlsafe(16)}"

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key and return user_id"""
    api_key = credentials.credentials
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return API_KEYS[api_key]

# ========================================
# AUTHENTICATION ENDPOINTS
# ========================================

@app.post("/api/auth/signup")
async def signup(user: UserSignup):
    """User registration endpoint"""

    # Check if user exists
    if user.email in [u["email"] for u in USERS_DB.values()]:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user_id = generate_user_id()
    api_key = generate_api_key()

    USERS_DB[user_id] = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "plan": user.plan,
        "created_at": datetime.now(),
        "subscription_status": "trial",  # Will integrate Stripe
        "products_tracked": 0
    }

    API_KEYS[api_key] = user_id

    return {
        "success": True,
        "user_id": user_id,
        "api_key": api_key,
        "message": "Account created successfully"
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """User login endpoint"""

    # Find user
    user = None
    for u in USERS_DB.values():
        if u["email"] == credentials.email and u["password"] == hash_password(credentials.password):
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Find or create API key
    api_key = None
    for key, uid in API_KEYS.items():
        if uid == user["id"]:
            api_key = key
            break

    if not api_key:
        api_key = generate_api_key()
        API_KEYS[api_key] = user["id"]

    return {
        "success": True,
        "api_key": api_key,
        "user_id": user["id"]
    }

# ========================================
# USER ENDPOINTS
# ========================================

@app.get("/api/user/profile")
async def get_profile(user_id: str = Depends(verify_api_key)):
    """Get user profile"""

    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan_limits = PLAN_LIMITS[user["plan"]]

    return UserProfile(
        id=user["id"],
        email=user["email"],
        plan=user["plan"],
        products_tracked=user["products_tracked"],
        products_limit=plan_limits["products"],
        created_at=user["created_at"],
        subscription_status=user["subscription_status"]
    )

@app.get("/api/user/stats")
async def get_stats(user_id: str = Depends(verify_api_key)):
    """Get dashboard statistics"""

    user_products = [p for p in PRODUCTS_DB.values() if p["user_id"] == user_id]

    # Calculate statistics
    total_products = len(user_products)
    active_alerts = len([a for a in ALERTS_DB.values() if a["user_id"] == user_id and a["enabled"]])

    # Get prices from last 24 hours
    yesterday = datetime.now() - timedelta(hours=24)
    recent_prices = [
        p for p in PRICES_DB.values()
        if p["user_id"] == user_id and p["timestamp"] > yesterday
    ]
    price_changes_24h = len(set(p["product_id"] for p in recent_prices))

    # Price statistics
    current_prices = [p["current_price"] for p in user_products if p.get("current_price")]
    avg_price = sum(current_prices) / len(current_prices) if current_prices else None
    lowest = min(current_prices) if current_prices else None
    highest = max(current_prices) if current_prices else None

    return DashboardStats(
        total_products=total_products,
        active_alerts=active_alerts,
        price_changes_24h=price_changes_24h,
        average_competitor_price=avg_price,
        lowest_price_found=lowest,
        highest_price_found=highest
    )

# ========================================
# PRODUCT ENDPOINTS
# ========================================

@app.post("/api/products/add")
async def add_product(product: ProductAdd, background_tasks: BackgroundTasks, user_id: str = Depends(verify_api_key)):
    """Add a product to track"""

    user = USERS_DB.get(user_id)
    plan_limits = PLAN_LIMITS[user["plan"]]

    # Check product limit
    if plan_limits["products"] != -1 and user["products_tracked"] >= plan_limits["products"]:
        raise HTTPException(
            status_code=403,
            detail=f"Product limit reached. Upgrade your plan to track more products."
        )

    # Create product
    product_id = generate_product_id()
    PRODUCTS_DB[product_id] = {
        "id": product_id,
        "user_id": user_id,
        "url": str(product.url),
        "name": product.name or "Unnamed Product",
        "competitor_name": product.competitor_name,
        "current_price": None,
        "last_checked": None,
        "alert_threshold": product.alert_threshold,
        "created_at": datetime.now()
    }

    # Update user count
    USERS_DB[user_id]["products_tracked"] += 1

    # Trigger immediate price check (background task)
    background_tasks.add_task(check_product_price, product_id)

    return {
        "success": True,
        "product_id": product_id,
        "message": "Product added successfully. Price check initiated."
    }

@app.get("/api/products/list")
async def list_products(user_id: str = Depends(verify_api_key)):
    """List all tracked products"""

    user_products = [
        ProductResponse(
            id=p["id"],
            url=p["url"],
            name=p["name"],
            current_price=p.get("current_price"),
            last_checked=p.get("last_checked"),
            price_history=get_price_history(p["id"]),
            competitor_name=p.get("competitor_name")
        )
        for p in PRODUCTS_DB.values()
        if p["user_id"] == user_id
    ]

    return {"products": user_products}

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str, user_id: str = Depends(verify_api_key)):
    """Delete a tracked product"""

    product = PRODUCTS_DB.get(product_id)
    if not product or product["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Product not found")

    del PRODUCTS_DB[product_id]
    USERS_DB[user_id]["products_tracked"] -= 1

    return {"success": True, "message": "Product deleted"}

# ========================================
# ALERT ENDPOINTS
# ========================================

@app.post("/api/alerts/configure")
async def configure_alert(alert: AlertConfig, user_id: str = Depends(verify_api_key)):
    """Configure price alert"""

    # Verify product ownership
    product = PRODUCTS_DB.get(alert.product_id)
    if not product or product["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Product not found")

    alert_id = f"alert_{secrets.token_urlsafe(16)}"
    ALERTS_DB[alert_id] = {
        "id": alert_id,
        "user_id": user_id,
        "product_id": alert.product_id,
        "alert_type": alert.alert_type,
        "threshold": alert.threshold,
        "enabled": alert.enabled,
        "created_at": datetime.now()
    }

    return {"success": True, "alert_id": alert_id}

@app.get("/api/alerts/list")
async def list_alerts(user_id: str = Depends(verify_api_key)):
    """List all configured alerts"""

    user_alerts = [a for a in ALERTS_DB.values() if a["user_id"] == user_id]
    return {"alerts": user_alerts}

# ========================================
# WEBHOOK ENDPOINTS (Premium feature)
# ========================================

@app.post("/api/webhooks/configure")
async def configure_webhook(webhook: WebhookConfig, user_id: str = Depends(verify_api_key)):
    """Configure webhook for price alerts (Professional+ only)"""

    user = USERS_DB.get(user_id)
    if user["plan"] not in [PlanTier.PROFESSIONAL, PlanTier.BUSINESS, PlanTier.ENTERPRISE]:
        raise HTTPException(status_code=403, detail="Webhooks require Professional plan or higher")

    # TODO: Implement webhook storage and triggers
    return {"success": True, "message": "Webhook configured"}

# ========================================
# ADMIN/BACKGROUND TASKS
# ========================================

async def check_product_price(product_id: str):
    """Background task to check product price (will be moved to Celery)"""
    # Placeholder - will implement actual scraping
    print(f"Checking price for product: {product_id}")
    # TODO: Implement Playwright scraping logic

def get_price_history(product_id: str) -> List[Dict[str, Any]]:
    """Get price history for a product"""
    history = [
        {
            "price": p["price"],
            "timestamp": p["timestamp"].isoformat(),
            "source": p.get("source", "scraper")
        }
        for p in PRICES_DB.values()
        if p["product_id"] == product_id
    ]
    return sorted(history, key=lambda x: x["timestamp"], reverse=True)

# ========================================
# HEALTH CHECK
# ========================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "service": "PriceWatch AI"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PriceWatch AI",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }

# ========================================
# STARTUP EVENT
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 PriceWatch AI API starting...")
    print("📊 Database: In-memory (will migrate to PostgreSQL)")
    print("✅ API Ready")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
