import os
from flask import Flask, request
import requests
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)

SYSTEM_PROMPT = """
أنت "وكيل ممدوح الذكي" - وسيط عقاري وتجاري محترف في دبي، الإمارات.
ترد باللهجة المصرية الخفيفة وباحترام، وتساعد العملاء في:
- بيع وشراء وتأجير العقارات السكنية والتجارية
- نصائح استثمار عقاري في دبي
- خدمات تجارية ووساطة
خلي ردودك قصيرة ومفيدة وودودة.
"""

def ask_ai(user_text):
    if not client:
        return "مفتاح OpenAI مش مضاف لسه، ضيف OPENAI_API_KEY في Render."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "حصل ضغط بسيط، جرب تاني كمان دقيقة 🙏"

@app.route("/")
def home():
    return "Bot is running! Mamdouh AI agent is live"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data)
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            reply = "وعليكم السلام ورحمة الله وبركاته 👋\nأنا وكيل ممدوح الذكي للسنوبر العقاري والتجاري، جاهز أخدمك. احكيلي عايز إيه؟"
        else:
            reply = ask_ai(text)

        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": reply})

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
