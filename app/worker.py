
import asyncio, json, logging
from openai import AsyncOpenAI
import redis.asyncio as redis
from .config import settings
from .channels.whatsapp import send_whatsapp
from .channels.telegram import send_telegram
from datetime import datetime

logger = logging.getLogger("worker")
openai_client = AsyncOpenAI(api_key=settings.OPENAI_KEY) if settings.OPENAI_KEY else None

TASK_QUEUE = asyncio.Queue()
STATS = {"processed": 0}

SYSTEM_TEMPLATE = """
أنت موظف المبيعات الخارق لشركة: {company_name}
معلومات الشركة: {company_info}
المنتجات: {products_info}

قواعد:
- رد بنفس لغة العميل باحترافية خليجية
- لا تقل أنك AI، اسمك سالم من قسم المبيعات
- هدفك: بيع أو حجز
- اذكر اسم العميل إن وجد
- اختم بسؤال يدفع للشراء
"""

async def ai_reply(company_name, company_info, products_info, memory, customer_msg, platform):
    if not openai_client:
        return "أهلاً بك! وصلتني رسالتك وسأرد عليك خلال دقيقة. تحب أحجز لك استشارة سريعة؟"
    try:
        system = SYSTEM_TEMPLATE.format(company_name=company_name, company_info=company_info, products_info=products_info)
        resp = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"ذاكرة: {memory}\nرسالة جديدة [{platform}]: {customer_msg}"}
            ],
            max_tokens=400, temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "أهلاً! سأعود لك بتفاصيل كاملة خلال لحظات."

async def worker_loop(redis_client: redis.Redis, db_session_factory):
    logger.info("🚀 Worker 24/7 Started")
    while True:
        try:
            task = await TASK_QUEUE.get()
            tenant = task["tenant"]
            platform = task["platform"]
            customer_id = task["customer_id"]
            message = task["message"]

            # الذاكرة
            mem_key = f"tenant:{tenant['id']}:memory:{customer_id}"
            memory = "عميل جديد"
            if redis_client:
                try:
                    data = await redis_client.get(mem_key)
                    if data:
                        history = json.loads(data)
                        memory = json.dumps(history[-3:], ensure_ascii=False)
                except:
                    pass

            reply = await ai_reply(tenant["company_name"], tenant["company_info"], tenant["products_info"], memory, message, platform)

            # حفظ الذاكرة
            if redis_client:
                try:
                    existing = await redis_client.get(mem_key)
                    hist = json.loads(existing) if existing else []
                    hist.append({"q": message, "a": reply, "t": datetime.now().isoformat()})
                    hist = hist[-20:]
                    await redis_client.set(mem_key, json.dumps(hist, ensure_ascii=False), ex=60*60*24*30)
                except:
                    pass

            # إرسال
            if platform == "whatsapp":
                await send_whatsapp(customer_id, reply, tenant["whatsapp_token"], tenant["whatsapp_phone_id"])
            else:
                await send_telegram(customer_id, reply, tenant["telegram_token"])

            # سجل
            try:
                db = db_session_factory()
                from .database import MessageLog
                log = MessageLog(tenant_id=tenant["id"], platform=platform, customer_id=customer_id, inbound=message, outbound=reply)
                db.add(log)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"DB log error: {e}")

            STATS["processed"] += 1
            TASK_QUEUE.task_done()
            await asyncio.sleep(0.3)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker self-healing: {e}")
            await asyncio.sleep(2)
