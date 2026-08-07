import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running! Mamdouh agent is live"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data) # عشان تشوفه في لوج Render
    
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text == "/start":
            reply_text = "وعليكم السلام ورحمة الله وبركاته! 👋\nأنا وكيل ممدوح الذكي للتسويق العقاري والتجاري، جاهز أخدمك. ابعتلي عايز ايه؟"
        elif "السلام" in text:
            reply_text = "وعليكم السلام يا غالي! تأمرني بإيه؟"
        else:
            reply_text = f"تمام، استلمت رسالتك: {text}\nأنا لسه بتعلم وهساعدك في التسويق قريب جداً."

        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply_text
        })
    
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
