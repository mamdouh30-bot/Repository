import os
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

SYSTEM_PROMPT = "أنت وكيل ممدوح الذكي - وسيط عقاري وتجاري محترف في دبي. ترد باللهجة المصرية الخفيفة وباحترام، وتساعد العملاء في البيع والشراء والتأجير والاستثمار العقاري في دبي. خلي ردودك قصيرة ومفيدة وودودة."

def ask_ai(user_text):
    if not OPENAI_API_KEY:
        return "مفتاح OpenAI مش مضاف لسه في Render."
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 400
        }
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=20)
        result = r.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI Error: {e}")
        return "حصل ضغط بسيط، جرب تاني بعد دقيقة 🙏"

@app.route("/")
def home():
    return "Bot is running! Mamdouh AI is live"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if text == "/start":
            reply = "وعليكم السلام ورحمة الله وبركاته 👋\nأنا وكيل ممدوح الذكي للوساطة العقارية والتجارية في دبي، جاهز أخدمك. احكيلي عايز إيه؟"
        else:
            reply = ask_ai(text)
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": reply})
    return "ok", 200
