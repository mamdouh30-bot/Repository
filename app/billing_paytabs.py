
"""
PayTabs Integration - دفع بالدرهم الإماراتي
الوثائق: https://dev.paytabs.com/
"""
import httpx
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db, Tenant, PaymentLog, gen_referral_code
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("paytabs")
router = APIRouter()

PAYTABS_API_URL = "https://secure.paytabs.com/payment/request"

@router.post("/create")
async def create_paytabs_payment(
    email: str,
    company_name: str,
    plan: str,
    ref: str = None,
    db: Session = Depends(get_db)
):
    if plan not in settings.PLANS:
        return JSONResponse({"error": "الخطة غير موجودة"}, status_code=400)

    plan_info = settings.PLANS[plan]
    amount = plan_info["price_aed"]

    # أنشئ المستأجر
    tenant = db.query(Tenant).filter(Tenant.email == email).first()
    if not tenant:
        # تحقق من كود الإحالة
        referred_by = None
        if ref:
            referred_by = db.query(Tenant).filter(Tenant.referral_code == ref).first()

        tenant = Tenant(
            company_name=company_name,
            email=email,
            plan=plan,
            referral_code=gen_referral_code(company_name),
            referred_by_id=referred_by.id if referred_by else None,
            trial_ends_at=datetime.utcnow()+timedelta(days=7)
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    # لو PayTabs غير مُعد، فعل تجريبي
    if not settings.PAYTABS_PROFILE_ID or not settings.PAYTABS_SERVER_KEY:
        tenant.is_active = True
        tenant.is_trial = True
        # مكافأة الإحالة
        if tenant.referred_by_id:
            referrer = db.query(Tenant).filter(Tenant.id == tenant.referred_by_id).first()
            if referrer:
                referrer.referral_count += 1
                referrer.free_months_earned += 1
                referrer.earnings_aed += 0  # الشهر المجاني ليس ربح مباشر لكنه يوفر
                db.commit()
                logger.info(f"Referral: {referrer.company_name} referred {tenant.company_name} -> +1 free month")

        db.add(PaymentLog(tenant_id=tenant.id, amount=0, currency="AED", method="trial", plan=plan, status="trial"))
        db.commit()
        return {"url": f"{settings.DOMAIN}/onboarding?tenant_id={tenant.id}&trial=true", "trial": True}

    # إنشاء صفحة دفع PayTabs حقيقية
    payload = {
        "profile_id": int(settings.PAYTABS_PROFILE_ID),
        "tran_type": "sale",
        "tran_class": "ecom",
        "cart_id": f"tenant_{tenant.id}_{plan}_{int(datetime.now().timestamp())}",
        "cart_currency": settings.PAYTABS_CURRENCY,
        "cart_amount": amount,
        "cart_description": f"اشتراك {plan_info['name']} - {company_name}",
        "paypage_lang": "ar",
        "callback": f"{settings.DOMAIN}/billing/paytabs/callback",
        "return": f"{settings.DOMAIN}/onboarding?tenant_id={tenant.id}",
        "customer_details": {
            "name": company_name,
            "email": email,
            "phone": "971500000000",
            "street1": "Dubai",
            "city": "Dubai",
            "state": "Dubai",
            "country": "AE",
            "zip": "00000"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                PAYTABS_API_URL,
                json=payload,
                headers={"Authorization": settings.PAYTABS_SERVER_KEY, "Content-Type": "application/json"},
                timeout=15
            )
            data = r.json()
            if data.get("redirect_url"):
                return {"url": data["redirect_url"]}
            else:
                logger.error(f"PayTabs error: {data}")
                # fallback
                tenant.is_active = True
                db.commit()
                return {"url": f"{settings.DOMAIN}/onboarding?tenant_id={tenant.id}&trial=true"}
    except Exception as e:
        logger.error(f"PayTabs exception: {e}")
        tenant.is_active = True
        db.commit()
        return {"url": f"{settings.DOMAIN}/onboarding?tenant_id={tenant.id}&trial=true"}

@router.post("/callback")
@router.get("/callback")
async def paytabs_callback(request: Request, db: Session = Depends(get_db)):
    # PayTabs يرسل callback بعد الدفع
    try:
        body = await request.json() if request.method == "POST" else dict(request.query_params)
        logger.info(f"PayTabs callback: {body}")

        cart_id = body.get("cart_id", "")
        if "tenant_" in cart_id:
            parts = cart_id.split("_")
            tenant_id = int(parts[1])
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                # تحقق من حالة الدفع
                if body.get("respStatus") in ["A", "Authorised", "APPROVED"] or body.get("payment_result", {}).get("response_status") == "A":
                    tenant.is_active = True
                    tenant.is_trial = False
                    tenant.paytabs_transaction_id = body.get("tran_ref") or body.get("transaction_id")

                    # سجل الدفع
                    amount = float(body.get("cart_amount") or body.get("tran_total") or settings.PLANS[tenant.plan]["price_aed"])
                    db.add(PaymentLog(tenant_id=tenant.id, amount=amount, currency="AED", method="paytabs", plan=tenant.plan, status="completed"))

                    # مكافأة الإحالة - شهر مجاني للمحيل
                    if tenant.referred_by_id:
                        referrer = db.query(Tenant).filter(Tenant.id == tenant.referred_by_id).first()
                        if referrer:
                            referrer.referral_count += 1
                            referrer.free_months_earned += 1
                            # احسب عمولة 20% كأرباح
                            referrer.earnings_aed += amount * 0.2

                    db.commit()
                    return RedirectResponse(f"{settings.DOMAIN}/onboarding?tenant_id={tenant.id}&paid=true")
    except Exception as e:
        logger.error(f"PayTabs callback error: {e}")

    return RedirectResponse(f"{settings.DOMAIN}/?payment=error")
