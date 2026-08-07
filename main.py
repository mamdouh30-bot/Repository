import os, logging, requests, random, datetime, json
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # مثلا @MamdouhEmpire او -100123456789
OWNER_ID = os.environ.get("OWNER_ID")  # ايدي تليجرام الخاص بك عشان التقارير
WEBHOOK_URL = "https://mamdouh-bot.onrender.com/webhook"

BOOKS = {
 "B0H9HVV2M5": "AI Digital Transformation - Book 18",
 "B0H98BH2MT": "AI Decision Making - Book 17",
 "B0H98NZ1NS": "AI Leadership - Book 16",
 "B0H94R5L7F": "AI Business Strategy - Book 15",
 "B0H8Z39WVC": "AI Project Management - Book 14",
 "B0H8XQMYLD": "AI Entrepreneurship - Book 13",
 "B0H8SWNSWW": "AI Human Resources - Book 12",
 "B0H8QD8TGG": "AI FINANCE - Book 11",
 "B0H8P7KJJX": "AI OPERATIONS - Book 10",
 "B0H8LW1LKX": "AI CUSTOMER SERVICE - Book 9",
 "B0H8HX9RRL": "AI AUTOMATION - Book 8",
 "B0H8FHN5WB": "AI SALES - Book 7",
 "B0H8324FGM": "AI Agents for Business - Book 6",
 "B0H7Z6QS6X": "AI Automation for Small Business - Book 5",
 "B0H7XFVFKV": "ULTIMATE AI PRODUCTIVITY HANDBOOK - Book 4",
 "B0H7Q4L27H": "The AI Advantage Guide - Book 3",
 "B0GYDN1RGV": "The AI Advantage Master - Book 2",
 "B0H7TB5VL5": "1000 AI Prompts for Business - Book 1",
 "B0H7MXSQ14": "Personal Finance Planner",
 "B0H7MF8GW2": "Homeowner Master Record Book",
 "B0H7BXPL95": "Home Maintenance Planner",
 "B0H75MRNHP": "Home Inventory Planner"
}

STORES = {
 "ballwool": "https://ballwool.com/shops/Bdran-Studio",
 "redbubble": "https://mamdouh-bdran.redbubble.com",
 "upwork": "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261"
}

# سجل الحملات المنشورة
PUBLISH_LOG = []

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000]}
        r = requests.post(url, json=payload, timeout=15)
        return r.json() if r.ok else None
    except Exception as e:
        logger.error(f"Send failed: {e}")
        return None

def publish_to_channel(text):
    if not CHANNEL_ID:
        return {"ok": False, "error": "CHANNEL_ID not set"}
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHANNEL_ID, "text": text[:4000]}
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if data.get("ok"):
            return {"ok": True, "message_id": data["result"]["message_id"]}
        return {"ok": False, "error": str(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def ask_ai_campaign(campaign_type="book", bid=None):
    if not GROQ_API_KEY:
        return "GROQ key missing"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        if campaign_type == "book":
            bid = bid or random.choice(list(BOOKS.keys()))
            system = "انت مسوق محترف. صمم حملة 4 سطور فقط: Hook + ميزة + سعر/قيمة + CTA + لينك في سطر منفصل. لا تستخدم markdown."
            user_p = f"حملة لكتاب {BOOKS[bid]} - لينك https://www.amazon.co.uk/dp/{bid} - متجري {STORES['ballwool']}"
        elif campaign_type == "ballwool":
            system = "مسوق لمتجر رقمي 28 منتج. اهم منتجات CRM Pro و LIFE OS و WEALTH OS. حملة 4 سطور Hook+Benefit+Price+CTA + لينك منفصل."
            user_p = f"حملة لمتجر Ballwool {STORES['ballwool']} - منتجات Business CRM Pro $24.99, LIFE OS 2.0, WEALTH OS $59.99"
        else:
            system = "مسوق لخدمة AI Workforce 7 وكلاء يردوا في 28 ثانية. حملة 4 سطور بالارقام."
            user_p = f"حملة لخدمة Upwork AI Workforce {STORES['upwork']} - 7 Agents - 28sec - 112 meeting/month - $12.3k saving"
        
        data = {"model": "llama-3.3-70b-versatile","messages": [{"role":"system","content":system},{"role":"user","content":user_p}],"temperature":0.8,"max_tokens":400}
        r = requests.post(url, headers=headers, json=data, timeout=25)
        if r.status_code==200:
            txt = r.json()["choices"][0]["message"]["content"]
            if campaign_type=="book":
                return txt, bid
            return txt, None
        return f"AI busy {r.status_code}", None
    except Exception as e:
        return f"Error {e}", None

def execute_full_campaign(trigger="auto"):
    """الوكيل المستقل ينفذ الحملة كاملة وينشر ويبلغ"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # اختار نوع الحملة بالتناوب
    day = datetime.datetime.now().day
    types = ["book", "ballwool", "upwork", "book"]
    ctype = types[day % len(types)]
    
    campaign_text, bid = ask_ai_campaign(ctype)
    
    # انشر في القناة
    publish_result = publish_to_channel(campaign_text)
    
    # سجل
    log_entry = {
        "time": now,
        "type": ctype,
        "book_id": bid,
        "text": campaign_text[:200],
        "published": publish_result.get("ok", False),
        "channel": CHANNEL_ID,
        "trigger": trigger
    }
    PUBLISH_LOG.append(log_entry)
    if len(PUBLISH_LOG) > 50:
        PUBLISH_LOG.pop(0)
    
    # تقرير للمالك
    report = f"""✅ الوكيل نفذ حملة {now}
📦 النوع: {ctype}
📚 المنتج: {BOOKS.get(bid, ctype) if bid else ctype}
📢 نشر: {'نعم في القناة ' + str(CHANNEL_ID) if publish_result.get('ok') else 'فشل - ' + str(publish_result.get('error'))}
📝 النص:
{campaign_text}

🔗 الروابط:
Amazon: https://www.amazon.co.uk/dp/{bid if bid else 'B0H8324FGM'}
Ballwool: {STORES['ballwool']}
Upwork: {STORES['upwork']}

📊 النتائج المتوقعة:
- وصول: 500-1000 مشاهدة في القناة
- نقرات متوقعة: 20-50 نقرة
- مبيعات محتملة: 1-3 (حسب تفاعل القناة)

السجل: /report
"""
    if OWNER_ID:
        send_telegram(OWNER_ID, report)
    
    return {"campaign": campaign_text, "log": log_entry, "report": report, "publish": publish_result}

@app.route("/")
def home():
    return jsonify({"status":"Live V8 Autonomous Agent","books":22,"channel":bool(CHANNEL_ID),"owner":bool(OWNER_ID),"logs":len(PUBLISH_LOG)})

@app.route("/setwebhook")
def set_webhook_route():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    return jsonify(requests.get(url, timeout=10).json())

@app.route("/autocampaign")
def autocampaign_route():
    result = execute_full_campaign(trigger="manual_api")
    return jsonify(result)

@app.route("/daily_push")
def daily_push():
    result = execute_full_campaign(trigger="cron_daily")
    return jsonify(result)

@app.route("/report")
def report_route():
    return jsonify({"total":len(PUBLISH_LOG),"logs":PUBLISH_LOG[-10:]})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data or "message" not in data:
            return "ok",200
        msg = data["message"]
        if "text" not in msg:
            return "ok",200
        chat_id = msg["chat"]["id"]
        text_raw = msg["text"]
        text = text_raw.lower()

        if "/autocampaign" in text or "نفذ حملة" in text or "ابدأ حملة" in text or "انشر نيابة" in text:
            send_telegram(chat_id, "🤖 الوكيل بدأ تنفيذ الحملة الآن... ثواني وينشر ويبلغك")
            result = execute_full_campaign(trigger=f"user_{chat_id}")
            send_telegram(chat_id, result["report"])
        
        elif "/report" in text or "ماذا فعلت" in text or "التقرير" in text or "النتائج" in text:
            if not PUBLISH_LOG:
                send_telegram(chat_id, "📭 لسه مفيش حملات منشورة. ابعت /autocampaign عشان ابدأ")
            else:
                last = PUBLISH_LOG[-1]
                txt = f"📊 آخر تقرير:\nالوقت: {last['time']}\nالنوع: {last['type']}\nنشر: {last['published']}\nالنص: {last['text']}\n\nإجمالي الحملات: {len(PUBLISH_LOG)}\n/report للتفاصيل"
                send_telegram(chat_id, txt)
        
        elif "/empire" in text:
            send_telegram(chat_id, f"امبراطوريتك 4 قنوات:\nAmazon 22 كتاب\nBallwool 28: {STORES['ballwool']}\nUpwork: {STORES['upwork']}\nRedbubble: {STORES['redbubble']}\n\nللبدء: /autocampaign")
        
        elif "/campaign" in text:
            ctext, _ = ask_ai_campaign("book")
            send_telegram(chat_id, ctext)
        
        else:
            # اي رسالة عامة = اعتبرها امر تنفيذ حملة
            if any(w in text for w in ["حملة", "انشر", "سوق", "campaign", "publish"]):
                send_telegram(chat_id, "🚀 فهمت! هابدأ حملة تسويقية كاملة وانشرها نيابة عنك...")
                result = execute_full_campaign(trigger=f"user_{chat_id}")
                send_telegram(chat_id, result["report"])
            else:
                ctext, _ = ask_ai_campaign("book")
                send_telegram(chat_id, ctext)

    except Exception as e:
        logger.error(e)
    return "ok",200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
