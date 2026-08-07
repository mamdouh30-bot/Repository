import os
import logging
import requests
from flask import Flask, request, jsonify

# --- إعدادات احترافية ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://mamdouh-bot.onrender.com/webhook"

# --- دوال أساسية ---
def send_telegram(chat_id, text):
    """إرسال رسالة مع حماية من الأخطاء"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
        r = requests.post(url, json=payload, timeout=15)
        logger.info(f"SendMessage: {r.status_code}")
        return r.ok
    except Exception as e:
        logger.error(f"Send Error: {e}")
        return False

def ask_ai(user_text):
    """سؤال Groq مع Fallback قوي"""
    if not GROQ_API_KEY:
        return "⚠️ مفتاح الـ AI مش متسجل في السيرفر (GROQ_API_KEY)"

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "أنت مساعد ذكي مصري اسمه ممدوح، خبير تسويق وبرمجة، ترد بالعامية المصرية باحترافية واختصار ومفيد جدا."},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        r = requests.post(url, headers=headers, json=data, timeout=25)
        logger.info(f"Groq Status: {r.status_code}")

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        elif r.status_code == 401:
            return "❌ مفتاح Groq غير صحيح أو منتهي. روح console.groq.com وهات مفتاح جديد."
        else:
            logger.error(r.text)
            return f"البوت شغال ✅ بس الـ AI مشغول حاليا (كود {r.status_code}). جرب تاني كمان ثانية."

    except Exception as e:
        logger.error(f"AI Exception: {e}")
        return f"البوت شغال ✅ بس حصل ضغط على الـ AI. جرب تاني: {user_text}"

# --- الروتات ---
@app.route("/")
def home():
    return jsonify({
        "status": "Live",
        "bot": "Mamdouh Bot V4 Pro",
        "groq_key_set": bool(GROQ_API_KEY),
        "bot_token_set": bool(BOT_TOKEN)
    })

@app.route("/setwebhook")
def set_webhook_route():
    """لتسهيل ربط الويب هوك بدون ما تكتب اللينك الطويل"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
        r = requests.get(url, timeout=10).json()
        return jsonify(r)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        logger.info(f"Incoming Update: {data}")

        if not data or "message" not in data:
            return "ok", 200

        message = data["message"]
        if "text" not in message:
            return "ok", 200

        chat_id = message["chat"]["id"]
        user_text = message["text"]

        # حركة typing عشان يبان احترافي
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction",
                          json={"chat_id": chat_id, "action": "typing"}, timeout=5)
        except: pass

        reply = ask_ai(user_text)
        send_telegram(chat_id, reply)

    except Exception as e:
        logger.error(f"Webhook Fatal: {e}")

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
