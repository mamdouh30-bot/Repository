
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .database import get_db, Tenant, PaymentLog, MessageLog
from .config import settings
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def check_admin(password: str):
    return password == settings.ADMIN_PASSWORD

@router.get("/", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    if not check_admin(password):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "كلمة السر خاطئة"})

    # الإحصائيات
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    total_messages = db.query(func.sum(Tenant.messages_used)).scalar() or 0
    total_revenue_aed = db.query(func.sum(PaymentLog.amount)).filter(PaymentLog.currency == "AED").scalar() or 0
    total_revenue_usd = db.query(func.sum(PaymentLog.amount)).filter(PaymentLog.currency == "USD").scalar() or 0

    # إيرادات اليوم
    today = datetime.utcnow().date()
    today_revenue = db.query(func.sum(PaymentLog.amount)).filter(func.date(PaymentLog.created_at) == today).scalar() or 0

    # MRR
    mrr_aed = 0
    for tenant in db.query(Tenant).filter(Tenant.is_active == True).all():
        mrr_aed += settings.PLANS.get(tenant.plan, {}).get("price_aed", 0)

    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    payments = db.query(PaymentLog).order_by(PaymentLog.created_at.desc()).limit(20).all()

    # أفضل المحيلين
    top_referrers = db.query(Tenant).filter(Tenant.referral_count > 0).order_by(Tenant.referral_count.desc()).limit(5).all()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "tenants": tenants,
        "payments": payments,
        "stats": {
            "total": total_tenants,
            "active": active_tenants,
            "messages": total_messages,
            "revenue_aed": total_revenue_aed,
            "revenue_usd": total_revenue_usd,
            "today": today_revenue,
            "mrr_aed": mrr_aed,
            "mrr_usd": mrr_aed / 3.67 if mrr_aed else 0
        },
        "top_referrers": top_referrers,
        "plans": settings.PLANS
    })

@router.get("/tenants", response_class=HTMLResponse)
async def admin_tenants_api(request: Request, password: str = "", db: Session = Depends(get_db)):
    # للـ API المباشر
    if password != settings.ADMIN_PASSWORD:
        return HTMLResponse("Unauthorized", status_code=401)
    tenants = db.query(Tenant).all()
    return {"tenants": [{"id": t.id, "company": t.company_name, "email": t.email, "plan": t.plan, "active": t.is_active, "messages": t.messages_used, "referral_code": t.referral_code, "referrals": t.referral_count} for t in tenants]}
