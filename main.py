import os, logging, requests, random, datetime
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
OWNER_ID = os.environ.get("OWNER_ID")
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
}

STORES = {
 "ballwool": "https://ballwool.com/shops/Bdran-Studio",
 "upwork": "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261"
}

PUBLISH_LOG = []

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": False}
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
        payload = {"chat_id": CHANNEL_ID, "text": text[:4000], "disable_web_page_preview": False}
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if data.get("ok"):
            return {"ok": True, "message_id": data["result"]["message_id"]}
        return {"ok": False, "error": str(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def ask_ai_campaign(campaign_type="book", bid=None):
    if not GROQ_API_KEY:
        return "GROQ key missing", None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        
        if campaign_type == "book":
            bid = bid or random.choice(list(BOOKS.keys()))
            title = BOOKS[bid]
            system = """You are a top-tier English copywriter for Amazon KDP. Write in PERFECT ENGLISH ONLY. 
Create a powerful marketing post for a business book. Structure:
Line 1: 🔥 HOOK with emoji (Stop wasting / Transform...)
Line 2: 💡 BENEFIT (What reader will learn/gain)
Line 3: 📚 VALUE + Social proof
Line 4: 👉 Strong CTA
Line 5: Blank line
Line 6: 🔗 Link alone

Keep it 4-5 lines max. Professional, persuasive, English only. No Arabic."""
            user_p = f"Write English campaign for book: {title}. Amazon link: https://www.amazon.co.uk/dp/{bid} . Also mention my store {STORES['ballwool']}"

        elif campaign_type == "ballwool":
            system = """You are an English copywriter for digital products. Write in PERFECT ENGLISH ONLY.
Store: Ballwool Bdran Studio with 28 premium Notion templates.
Top products: Business CRM Pro $24.99, LIFE OS 2.0, WEALTH OS $59.99.
Structure:
🚀 HOOK
💼 BENEFIT (organize business, save 10+ hours/week)
💰 PRICE + VALUE
👉 CTA
Link separate line.
English only, 4-5 lines, no Arabic."""
            user_p = f"Write English campaign for Ballwool store {STORES['ballwool']} - Focus on Business CRM Pro and LIFE OS"

        else: # upwork
            system = """You are an English copywriter for AI automation agency.
Service: AI Workforce with 7 AI Agents, responds in 28 seconds, books 112 meetings/month, saves $12.3k/month.
Structure:
🤖 HOOK about AI workforce
⚡ BENEFIT with numbers
💰 ROI/Savings
👉 CTA to hire on Upwork
Link separate.
Perfect English only, no Arabic, 4-5 lines."""
            user_p = f"Write English campaign for Upwork AI Workforce service: {STORES['upwork']}"

        data = {"model": "llama-3.3-70b-versatile","messages": [{"role":"system","content":system},{"role":"user","content":user_p}],"temperature":0.85,"max_tokens":500}
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code==200:
            txt = r.json()["choices"][0]["message"]["content"]
            if campaign_type=="book":
                return txt, bid
            return txt, None
        return f"AI busy {r.status_code}", None
    except Exception as e:
        return f"Error {e}", None

def execute_full_campaign(trigger="auto"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    day = datetime.datetime.now().day
    types = ["book", "ballwool", "upwork", "book", "book"]
    ctype = types[day % len(types)]
    
    campaign_text, bid = ask_ai_campaign(ctype)
    
    publish_result = publish_to_channel(campaign_text)
    
    log_entry = {
        "time": now,
        "type": ctype,
        "book_id": bid,
        "text": campaign_text[:250],
        "published": publish_result.get("ok", False),
        "channel": CHANNEL_ID,
        "trigger": trigger
    }
    PUBLISH_LOG.append(log_entry)
    if len(PUBLISH_LOG) > 50:
        PUBLISH_LOG.pop(0)
    
    # تقرير عربي للمالك لكن الحملة انجليزي
    report = f"""✅ Campaign Executed {now} - ENGLISH
📦 Type: {ctype}
📚 Product: {BOOKS.get(bid, ctype) if bid else ctype}
📢 Published: {'YES in ' + str(CHANNEL_ID) if publish_result.get('ok') else 'FAILED - ' + str(publish_result.get('error'))}

📝 ENGLISH POST:
{campaign_text}

🔗 Links:
Amazon: https://www.amazon.co.uk/dp/{bid if bid else 'B0H8324FGM'}
Ballwool: {STORES['ballwool']}
Upwork: {STORES['upwork']}

📊 Expected:
- Reach: 500-1000 views
- Clicks: 20-50
- Sales: 1-3

Channel: https://t.me/dukkan_mamdouh
"""
    if OWNER_ID:
        send_telegram(OWNER_ID, report)
    
    return {"campaign": campaign_text, "log": log_entry, "report": report, "publish": publish_result}

@app.route("/")
def home():
    return jsonify({"status":"Live V9 ENGLISH Campaigns","channel":CHANNEL_ID,"english_mode":True,"logs":len(PUBLISH_LOG)})

@app.route("/setwebhook")
def set_webhook_route():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    return jsonify(requests.get(url, timeout=10).json())

@app.route("/autocampaign")
def autocampaign_route():
    result = execute_full_campaign(trigger="manual_api")
    return jsonify(result)

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

        if "/autocampaign" in text or "english" in text:
            send_telegram(chat_id, "🤖 Starting ENGLISH campaign... publishing to @dukkan_mamdouh in seconds...")
            result = execute_full_campaign(trigger=f"user_{chat_id}")
            send_telegram(chat_id, result["report"])
        
        elif "/report" in text:
            if not PUBLISH_LOG:
                send_telegram(chat_id, "📭 No campaigns yet. Send /autocampaign")
            else:
                last = PUBLISH_LOG[-1]
                send_telegram(chat_id, f"📊 Last: {last['time']} | {last['type']} | Published: {last['published']}\n{last['text']}")
        
        elif "/campaign" in text:
            ctext, _ = ask_ai_campaign("book")
            publish_to_channel(ctext)
            send_telegram(chat_id, f"✅ Published ENGLISH campaign to channel:\n\n{ctext}")
        
        else:
            if any(w in text for w in ["campaign", "publish", "انشر", "حملة"]):
                send_telegram(chat_id, "🚀 Got it! Creating ENGLISH campaign for @dukkan_mamdouh...")
                result = execute_full_campaign(trigger=f"user_{chat_id}")
                send_telegram(chat_id, result["report"])

    except Exception as e:
        logger.error(e)
    return "ok",200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
