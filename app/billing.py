
import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db, Tenant
import os
from datetime import datetime, timedelta

stripe.api_key = settings.STRIPE_SECRET
router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout(email: str, company_name: str, plan: str, db: Session = Depends(get_db)):
    # Normalize plan names (support both old and new)
    plan_map = {
        "basic": "starter",
        "starter": "starter",
        "pro": "growth",
        "growth": "growth",
        "enterprise": "empire",
        "empire": "empire"
    }
    normalized_plan = plan_map.get(plan, plan)
    if normalized_plan not in settings.PLANS:
        normalized_plan = "growth"  # default
    
    price_map = {
        "starter": settings.PRICE_BASIC,
        "growth": settings.PRICE_GROWTH,
        "empire": settings.PRICE_EMPIRE,
        "basic": settings.PRICE_BASIC,
        "pro": settings.PRICE_GROWTH,
        "enterprise": settings.PRICE_EMPIRE
    }

    # أنشئ أو احصل على العميل
    tenant = db.query(Tenant).filter(Tenant.email == email).first()
    if not tenant:
        tenant = Tenant(company_name=company_name, email=email, plan=normalized_plan, trial_ends_at=datetime.utcnow()+timedelta(days=7))
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    else:
        tenant.plan = normalized_plan
        db.commit()

    try:
        # في وضع التجربة بدون Stripe حقيقي - استخدم DOMAIN من الإعدادات
        domain = settings.DOMAIN.rstrip("/")
        if domain == "http://localhost:8000":
            # حاول قراءة من Railway domain تلقائياً
            domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", domain)
            if not domain.startswith("http"):
                domain = f"https://{domain}" if domain else "https://repository-production-f279.up.railway.app"
        
        if not settings.STRIPE_SECRET or "sk_" not in str(settings.STRIPE_SECRET):
            # تفعيل تجريبي مجاني 7 أيام
            tenant.is_active = True
            tenant.is_trial = True
            db.commit()
            return {"url": f"{domain}/onboarding?tenant_id={tenant.id}&trial=true", "trial": True}

        checkout_session = stripe.checkout.Session.create(
            customer_email=email,
            line_items=[{"price": price_map.get(plan, price_map["growth"]), "quantity": 1}],
            mode="subscription",
            success_url=f"{domain}/onboarding?tenant_id={tenant.id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/?canceled=true",
            metadata={"tenant_id": str(tenant.id), "plan": normalized_plan}
        )
        return {"url": checkout_session.url}
    except Exception as e:
        print(f"Stripe error: {e}")
        # fallback للتجربة
        tenant.is_active = True
        db.commit()
        domain = settings.DOMAIN.rstrip("/").replace("http://localhost:8000", "https://repository-production-f279.up.railway.app")
        return {"url": f"{domain}/onboarding?tenant_id={tenant.id}&trial=true"}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        else:
            event = stripe.Event.construct_from(await request.json(), stripe.api_key)
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        tenant_id = session["metadata"].get("tenant_id")
        tenant = db.query(Tenant).filter(Tenant.id == int(tenant_id)).first() if tenant_id else None
        if tenant:
            tenant.is_active = True
            tenant.is_trial = False
            tenant.stripe_customer_id = session.get("customer")
            tenant.stripe_subscription_id = session.get("subscription")
            db.commit()
            print(f"✅ Tenant {tenant.company_name} activated - {tenant.plan}")

    elif event["type"] == "customer.subscription.deleted":
        sub_id = event["data"]["object"]["id"]
        tenant = db.query(Tenant).filter(Tenant.stripe_subscription_id == sub_id).first()
        if tenant:
            tenant.is_active = False
            db.commit()

    return {"status": "ok"}
