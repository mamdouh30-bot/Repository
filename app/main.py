
"""
Super Employee OS - النسخة النهائية SaaS
منتج جاهز للبيع باشتراك شهري
"""
import asyncio
from fastapi import FastAPI, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import redis.asyncio as redis
import logging
from contextlib import asynccontextmanager

from .config import settings
from .database import get_db, Tenant, SessionLocal, Base, engine
from .billing import router as billing_router
from .worker import TASK_QUEUE, worker_loop, STATS
from .channels.whatsapp import send_whatsapp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

redis_client = None
worker_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, worker_task
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Redis OK")
    except:
        redis_client = None
        logger.warning("⚠️ Redis memory-only mode")

    def db_factory():
        return SessionLocal()

    worker_task = asyncio.create_task(worker_loop(redis_client, db_factory))
    yield
    worker_task.cancel()
    if redis_client:
        await redis_client.close()

app = FastAPI(title="Super Employee SaaS", lifespan=lifespan)
app.include_router(billing_router, prefix="/billing", tags=["billing"])

templates = Jinja2Templates(directory="templates")

# ========== صفحات العميل ==========
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "plans": settings.PLANS, "publishable_key": settings.STRIPE_PUBLISHABLE, "domain": settings.DOMAIN})

@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request, tenant_id: int = Query(...), db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return HTMLResponse("الشركة غير موجودة", status_code=404)
    if not tenant.is_active:
        return HTMLResponse("الاشتراك غير نشط - يرجى الدفع", status_code=403)
    return templates.TemplateResponse("onboarding.html", {"request": request, "tenant": tenant})

@app.post("/onboarding/save")
async def save_onboarding(
    tenant_id: int = Form(...),
    whatsapp_token: str = Form(""),
    whatsapp_phone_id: str = Form(""),
    telegram_token: str = Form(""),
    company_info: str = Form(""),
    products_info: str = Form(""),
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return JSONResponse({"error": "not found"}, status_code=404)
    tenant.whatsapp_token = whatsapp_token
    tenant.whatsapp_phone_id = whatsapp_phone_id
    tenant.telegram_token = telegram_token
    tenant.company_info = company_info
    tenant.products_info = products_info
    db.commit()
    return RedirectResponse(f"/dashboard/{tenant.id}", status_code=302)

@app.get("/dashboard/{tenant_id}", response_class=HTMLResponse)
async def dashboard(request: Request, tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return HTMLResponse("غير موجود", status_code=404)
    return templates.TemplateResponse("dashboard.html", {"request": request, "tenant": tenant, "stats": STATS, "queue": TASK_QUEUE.qsize()})

# ========== Webhooks متعددة المستأجرين ==========
@app.get("/webhook/whatsapp/{tenant_id}")
async def verify_whatsapp_tenant(tenant_id: int, request: Request, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return PlainTextResponse("Tenant not found", status_code=404)
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    # كل مستأجر له verify token = super_employee_{id}
    expected = f"super_employee_{tenant_id}"
    if mode == "subscribe" and token == expected:
        return PlainTextResponse(challenge, status_code=200)
    return PlainTextResponse("Forbidden", status_code=403)

@app.post("/webhook/whatsapp/{tenant_id}")
async def receive_whatsapp_tenant(tenant_id: int, request: Request, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.is_active:
        return JSONResponse({"status": "inactive"}, status_code=200)

    # حد الاستخدام
    plan_limit = settings.PLANS.get(tenant.plan, {}).get("limit", 1000)
    if tenant.messages_used >= plan_limit:
        return JSONResponse({"status": "limit reached"}, status_code=200)

    try:
        body = await request.json()
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        messages = changes.get("value", {}).get("messages", [])
        for msg in messages:
            if msg.get("type") == "text":
                await TASK_QUEUE.put({
                    "tenant": {"id": tenant.id, "company_name": tenant.company_name, "company_info": tenant.company_info, "products_info": tenant.products_info, "whatsapp_token": tenant.whatsapp_token, "whatsapp_phone_id": tenant.whatsapp_phone_id, "telegram_token": tenant.telegram_token},
                    "platform": "whatsapp",
                    "customer_id": msg.get("from"),
                    "message": msg.get("text", {}).get("body", "")
                })
                tenant.messages_used += 1
        db.commit()
        return JSONResponse({"status": "queued"})
    except Exception as e:
        logger.error(f"WA tenant {tenant_id} error: {e}")
        return JSONResponse({"status": "ok"}, status_code=200)

@app.post("/webhook/telegram/{tenant_id}")
async def receive_telegram_tenant(tenant_id: int, request: Request, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or not tenant.is_active:
        return JSONResponse({"status": "inactive"}, status_code=200)
    try:
        body = await request.json()
        message = body.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        if not chat_id or not text:
            return JSONResponse({"status": "ignored"})
        await TASK_QUEUE.put({
            "tenant": {"id": tenant.id, "company_name": tenant.company_name, "company_info": tenant.company_info, "products_info": tenant.products_info, "whatsapp_token": tenant.whatsapp_token, "whatsapp_phone_id": tenant.whatsapp_phone_id, "telegram_token": tenant.telegram_token},
            "platform": "telegram",
            "customer_id": chat_id,
            "message": text
        })
        tenant.messages_used += 1
        db.commit()
        return JSONResponse({"status": "queued"})
    except Exception as e:
        logger.error(f"TG tenant {tenant_id} error: {e}")
        return JSONResponse({"status": "ok"}, status_code=200)

# ========== الصحة والإحصائيات ==========
@app.get("/health")
async def health():
    return {"status": "ok", "worker": "alive", "queue": TASK_QUEUE.qsize(), "processed": STATS["processed"], "time": datetime.now().isoformat()}

@app.get("/admin/tenants")
async def admin_tenants(db: Session = Depends(get_db)):
    # احميها بكلمة سر في الإنتاج - هنا مبسطة
    tenants = db.query(Tenant).all()
    return [{"id": t.id, "company": t.company_name, "email": t.email, "plan": t.plan, "active": t.is_active, "messages": t.messages_used, "created": t.created_at} for t in tenants]
