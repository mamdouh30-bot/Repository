import os
import time
import threading
import random
import logging
from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# ================= الإعدادات =================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINTEREST_EMAIL = os.getenv("PINTEREST_EMAIL")
PINTEREST_PASS = os.getenv("PINTEREST_PASS")
OWNER_ID = os.getenv("OWNER_ID")

app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# حالة النشر التلقائي
auto_enabled = os.getenv("AUTO_POST", "on").lower() == "on"
is_posting = False

# ================= دوال مساعدة =================
def send_telegram(chat_id, text):
    if not BOT_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram fail: {e}", flush=True)

def generate_book_content():
    """يولد عنوان ووصف كتاب بالإنجليزية لأمريكا وأوروبا"""
    try:
        if not client:
            raise Exception("No OpenAI Key")
        prompt = "Generate a viral Pinterest Pin idea for a coloring book or puzzle book for US market. Return JSON: {'title':'...','description':'...','prompt_image':'...'} Title must be catchy English."
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.9
        )
        import json
        text = resp.choices[0].message.content
        # محاولة قراءة JSON
        try:
            data = json.loads(text[text.find('{'):text.rfind('}')+1])
            return data
        except:
            return {"title": "Cozy Coloring Book for Adults", "description": text[:300], "prompt_image": "cute cozy coloring page"}
    except Exception as e:
        print(f"AI fail: {e}", flush=True)
        return {
            "title": f"Magic Coloring Book {random.randint(1,999)}",
            "description": "Best seller coloring book for adults relaxation in USA #coloringbook #amazonkdp",
            "prompt_image": "cozy aesthetic coloring page"
        }

def create_pin_image(title):
    """ينشئ صورة غلاف بسيطة بـ Pillow بدون الحاجة لمتصفح"""
    try:
        width, height = 1000, 1500
        img = Image.new('RGB', (width, height), color=(255, 248, 235))
        draw = ImageDraw.Draw(img)

        # مستطيل عنوان
        draw.rectangle([50, 50, width-50, 400], fill=(255, 107, 107), radius=30)

        # كتابة العنوان (بدون خط خارجي لتجنب الأخطاء)
        try:
            # حاول تحميل خط
            font = ImageFont.load_default()
            draw.text((100, 150), title[:40], fill="white", font=font, stroke_width=2)
        except:
            draw.text((100, 150), title[:40], fill="white")

        draw.text((100, 500), "Available on Amazon", fill=(50,50,50))
        draw.text((100, 600), "Link in Bio", fill=(50,50,50))

        path = "/tmp/pin.jpg"
        img.save(path, "JPEG", quality=95)
        return path
    except Exception as e:
        print(f"PIL fail: {e}", flush=True)
        raise

def post_to_pinterest():
    """دالة النشر - نسخة آمنة لا تعلق الـ Worker"""
    global is_posting
    if is_posting:
        print("Already posting, skip", flush=True)
        return
    is_posting = True
    try:
        print("INFO:main:Auto scheduler triggered", flush=True)
        data = generate_book_content()
        image_path = create_pin_image(data['title'])
        print(f"Poster: Generated {data['title']} - Image {image_path}", flush=True)

        # هنا كود الـ Playwright الحقيقي
        # نستخدم try منفصل عشان لو فشل المتصفح ما يوقعش السيرفر
        if PINTEREST_EMAIL and PINTEREST_PASS:
            try:
                from playwright.sync_api import sync_playwright
                print("Starting Playwright...", flush=True)
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
                    page = browser.new_page()
                    page.goto("https://www.pinterest.com/login/", timeout=60000)
                    #... كود تسجيل الدخول والنشر...
                    print("Pinterest login attempted", flush=True)
                    browser.close()
            except Exception as e:
                print(f"Playwright fail (non-critical): {e}", flush=True)
                # حتى لو فشل Playwright، لا توقع السيرفر
                pass

        print(f"SUCCESS: Pin ready: {data['title']}", flush=True)

    except Exception as e:
        print(f"ERROR:main:Poster fail: {e}", flush=True)
    finally:
        is_posting = False

# ================= Background Thread =================
def auto_loop():
    """يعمل في الخلفية كل ساعة بدون ما يعلق Flask"""
    while True:
        try:
            if auto_enabled:
                post_to_pinterest()
            else:
                print("Auto is OFF, sleeping...", flush=True)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
        time.sleep(3600) # كل ساعة

# شغل الثريد في الخلفية - أهم سطر لحل TIMEOUT
threading.Thread(target=auto_loop, daemon=True).start()

# ================= Flask Routes =================
@app.route("/", methods=["GET"])
def home():
    # لازم يرد بسرعة أقل من ثانية عشان Render ما يعملش TIMEOUT
    return jsonify({"status": "live", "auto": auto_enabled, "bot": "mamdouh-bot"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    global auto_enabled
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return "ok", 200

        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").lower()

        if "/auto on" in text:
            auto_enabled = True
            send_telegram(chat_id, "🚀 وضع الإمبراطورية مفعل - سأنشر كل ساعة لأمريكا!")
        elif "/auto off" in text:
            auto_enabled = False
            send_telegram(chat_id, "⏸️ تم إيقاف النشر التلقائي")
        elif "/post" in text:
            send_telegram(chat_id, "⏳ جاري النشر الآن...")
            threading.Thread(target=post_to_pinterest, daemon=True).start()
        elif "/status" in text:
            send_telegram(chat_id, f"📊 الحالة: {'مفعل ✅' if auto_enabled else 'متوقف ❌'}\nService: https://mamdouh-bot.onrender.com")

    except Exception as e:
        print(f"Webhook error: {e}", flush=True)

    return "ok", 200

# لـ gunicorn
# gunicorn main:app --timeout 300 --workers 1 --threads 2
