from flask import Flask, request
import os, requests
app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

@app.route("/")
def home(): return "Bot Live"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data)
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text","")
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": chat_id, "text": f"البوت شغال ✅ وصلني: {text}"})
    return "ok"

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
