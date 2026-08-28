
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./saas.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me-123456789")
    DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

    # Stripe
    STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC", "price_basic")
    PRICE_GROWTH = os.getenv("STRIPE_PRICE_GROWTH", "price_growth")
    PRICE_EMPIRE = os.getenv("STRIPE_PRICE_EMPIRE", "price_empire")

    
    PLANS = {
        "starter": {"name": "البداية", "price": 99, "limit": 1000, "features": ["1,000 رسالة", "رد خليجي", "ذاكرة عملاء"]},
        "growth": {"name": "النمو", "price": 199, "limit": 5000, "features": ["5,000 رسالة", "نشر تلقائي", "ربط المتجر", "تقارير يومية"]},
        "empire": {"name": "الإمبراطورية", "price": 299, "limit": 999999, "features": ["رسائل غير محدودة", "3 أرقام", "تدريب AI", "API خاص"]},
        # legacy keys for billing compatibility
        "basic": {"name": "البداية", "price": 99, "limit": 1000, "features": []},
        "pro": {"name": "النمو", "price": 199, "limit": 5000, "features": []},
        "enterprise": {"name": "الإمبراطورية", "price": 299, "limit": 999999, "features": []},
    }


settings = Settings()
