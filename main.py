import os
import time
import threading
import random
import logging
from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINTEREST_EMAIL = os.getenv("PINTEREST_EMAIL")
PINTEREST_PASS = os.getenv("PINTEREST_PASS")

app = Flask(__name__)

try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except:
    client = None

auto_enabled = True
is_posting = False

def send_telegram(chat_id, text):
    if not BOT_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram fail: {e}", flush=True)

def generate_book_content():
    try:
        if client:
            prompt = "Generate viral Pinterest pin for coloring book US market. JSON: {'title':'...','description':'...'}"
            resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.9)
            import json
            txt = resp.choices[0].message.content
            try:
                data = json.loads(txt[txt.find('{'):txt.rfind('}')+1])
                return data
            except:
                pass
    except Exception as e:
        print(f"AI fail: {e}", flush=True)
    return {"title": f"Cozy Coloring Book {random.randint(1,999)}", "description": "Best seller coloring book for adults relaxation USA #coloringbook"}

def create_pin_image(title):
    try:
        w, h = 1000, 1500
        img = Image.new('RGB', (w, h), color=(255, 248, 235))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, w-50, 400], fill=(255, 107, 107))
        font = ImageFont.load_default()
        draw.text((100, 150), title[:40], fill="white", font=font)
        draw.text((100, 500), "Available on Amazon", fill=(50,50,50))
        path = "/tmp/pin.jpg"
        img.save(path, "JPEG", quality=95)
        return path
    except Exception as e:
        print(f"PIL fail: {e}", flush=True)
        raise

def post_to_pinterest():
    global is_posting
    if is_posting: return
    is_posting = True
    try:
        print("INFO:main:Auto scheduler triggered", flush=True)
        data = generate_book_content()
        image_path = create_pin_image(data['title'])
        print(f"SUCCESS: Pin ready: {data['title']} Image:{image_path}", flush=True)
    except Exception as e:
        print(f"ERROR:main:Poster fail: {e}", flush=True)
    finally:
        is_posting = False

def auto_loop():
    while True:
        try:
            if auto_enabled:
                post_to_pinterest()
        except Exception as e:
            print(f"Loop error: {e}", flush=True)
        time.sleep(3600)

threading.Thread(target=auto_loop, daemon=True).start()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "live", "auto": auto_enabled}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    global auto_enabled
    try:
        data = request.get_json()
        if not data or "message" not in data: return "ok", 200
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text","").lower()
        if "/auto on" in text:
            auto_enabled = True
            send_telegram(chat_id, "🚀 وضع الإمبراطورية مفعل!")
        elif "/auto off" in text:
            auto_enabled = False
            send_telegram(chat_id, "⏸️ تم الإيقاف")
        elif "/post" in text:
            send_telegram(chat_id, "⏳ جاري النشر...")
            threading.Thread(target=post_to_pinterest, daemon=True).start()
        elif "/status" in text:
            send_telegram(chat_id, f"📊 الحالة: {'مفعل ✅' if auto_enabled else 'متوقف ❌'}")
    except Exception as e:
        print(f"Webhook error: {e}", flush=True)
    return "ok", 200
