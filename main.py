import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ mamdouh-bot is Online 24/7 - Powered by Render"

@app.route('/health')
def health():
    return "OK", 200

# ========== هنا تحط كود البوت بتاعك ==========
# مثال لبوت تليجرام، لو عندك بوت تاني استبدل اللي تحت
def run_bot_logic():
    print("🚀 Bot logic is running...")
    # مثال: لو عندك بوت تليجرام حط الكود هنا
    # import telebot
    # bot = telebot.TeleBot(os.environ.get("BOT_TOKEN"))
    # bot.infinity_polling()
    
    # لو معندكش بوت دلوقتي، خليها شغالة كده عشان السيرفر يفضل حي
    while True:
        pass

# ===========================================

if __name__ == "__main__":
    # شغل البوت في الخلفية
    bot_thread = threading.Thread(target=run_bot_logic, daemon=True)
    bot_thread.start()
    
    # ده السيرفر اللي Render محتاجه عشان يعرف انك شغال
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
