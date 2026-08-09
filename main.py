import os, time, threading, random, logging, requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINTEREST_EMAIL = os.getenv("PINTEREST_EMAIL")
PINTEREST_PASS = os.getenv("PINTEREST_PASS")
PINTEREST_BOARD = os.getenv("PINTEREST_BOARD", "coloring")
OWNER_ID = os.getenv("OWNER_ID") # ال ID بتاعك من @userinfobot
GROUP_ID = os.getenv("GROUP_ID") # اي دي الجروب - مثال -100123456789

auto_enabled = True
is_posting = False

def send_text(chat_id, text):
    if not BOT_TOKEN or not chat_id: return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except: pass

def send_photo(chat_id, path, caption):
    if not BOT_TOKEN or not chat_id: return
    try:
        with open(path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data={"chat_id": chat_id, "caption": caption}, files={"photo": f}, timeout=30)
    except Exception as e:
        print(f"Send photo fail {chat_id}: {e}", flush=True)

def generate_content():
    import json
    try:
        from groq import Groq
        if GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"):
            c = Groq(api_key=GROQ_API_KEY)
            r = c.chat.completions.create(model="llama3-8b-8192", messages=[{"role":"user","content":"Give viral Pinterest Pin for US coloring books. ONLY JSON {\"title\":\"short catchy title\",\"description\":\"SEO description with hashtags\"}"}], temperature=0.9)
            txt = r.choices[0].message.content
            return json.loads(txt[txt.find('{'):txt.rfind('}')+1])
    except Exception as e:
        print(f"AI fail: {e}", flush=True)
    return {"title": f"Cozy Coloring Book {random.randint(1,999)}", "description": "Relaxing coloring book for adults USA #coloringbook #amazonfinds"}

def create_image(title):
    w,h = 1000,1500
    img = Image.new('RGB',(w,h),color=(255,248,235))
    d = ImageDraw.Draw(img)
    d.rectangle([50,50,w-50,400],fill=(255,107,107))
    f = ImageFont.load_default()
    d.text((80,150),title[:45],fill="white",font=f)
    d.text((80,500),"Available on Amazon",fill=(30,30,30),font=f)
    p="/tmp/pin.jpg"
    img.save(p,"JPEG",quality=95)
    return p

def publish_pinterest(image_path, title, description):
    if not PINTEREST_EMAIL or not PINTEREST_PASS:
        print("Pinterest creds missing", flush=True)
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=['--no-sandbox','--disable-blink-features=AutomationControlled'])
            context = browser.new_context()
            page = context.new_page()
            print("Pinterest: opening login", flush=True)
            page.goto("https://www.pinterest.com/login/", timeout=90000)
            page.wait_for_timeout(3000)
            # تسجيل دخول
            try:
                page.fill('input#email', PINTEREST_EMAIL)
                page.fill('input#password', PINTEREST_PASS)
                page.click('button[type="submit"]')
            except:
                page.fill('input[name="id"]', PINTEREST_EMAIL)
                page.fill('input[name="password"]', PINTEREST_PASS)
                page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            print("Pinterest: logged in, opening builder", flush=True)
            page.goto("https://www.pinterest.com/pin-builder/", timeout=90000)
            page.wait_for_timeout(5000)
            # رفع الصورة
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(image_path)
            page.wait_for_timeout(5000)
            # عنوان ووصف
            try:
                page.fill('input[placeholder*="Add your title"]', title[:100])
                page.fill('textarea[placeholder*="Tell everyone"]', description[:500])
            except Exception as e:
                print(f"Fill fail: {e}", flush=True)
            page.wait_for_timeout(3000)
            # اختيار البورد ونشر
            try:
                # يدور على زر اختيار البورد
                page.locator('div:has-text("Select a board")').first.click(timeout=10000)
                page.wait_for_timeout(2000)
                # يختار اول بورد فيه الكلمة
                if PINTEREST_BOARD:
                    page.locator(f'div:has-text("{PINTEREST_BOARD}")').first.click(timeout=5000)
                else:
                    page.locator('[data-test-id="board-row"]').first.click(timeout=5000)
                page.wait_for_timeout(2000)
                page.locator('div:has-text("Publish")').last.click(timeout=10000)
                print("Pinterest: Publish clicked", flush=True)
                page.wait_for_timeout(8000)
            except Exception as e:
                print(f"Board/Publish fail: {e}", flush=True)
                page.screenshot(path="/tmp/pinterest_fail.png")
            browser.close()
            return True
    except Exception as e:
        print(f"Pinterest fatal: {e}", flush=True)
        return False

def run_post(trigger_chat_id=None):
    global is_posting
    if is_posting: return
    is_posting = True
    try:
        data = generate_content()
        img_path = create_image(data['title'])
        caption = f"{data['title']}\n\n{data['description']}"

        # 1- نشر في تليجرام
        targets = []
        if trigger_chat_id: targets.append(trigger_chat_id)
        if OWNER_ID: targets.append(OWNER_ID)
        if GROUP_ID: targets.append(GROUP_ID)
        # ازالة التكرار
        targets = list(set(targets))
        for tid in targets:
            send_photo(tid, img_path, caption)

        print(f"SUCCESS: Pin ready {data['title']}", flush=True)

        # 2- نشر في Pinterest في الخلفية (مش هيوقع البوت)
        ok = publish_pinterest(img_path, data['title'], data['description'])
        if ok and trigger_chat_id:
            send_text(trigger_chat_id, "✅ تم النشر في Pinterest بنجاح!")
        elif not ok and trigger_chat_id:
            send_text(trigger_chat_id, "⚠️ تم النشر في تليجرام لكن Pinterest احتاج تسجيل دخول يدوي اول مرة")

    except Exception as e:
        print(f"Poster fail: {e}", flush=True)
    finally:
        is_posting = False

def auto_loop():
    while True:
        try:
            if auto_enabled:
                run_post()
        except: pass
        time.sleep(3600)

threading.Thread(target=auto_loop, daemon=True).start()

@app.route("/")
def home(): return jsonify({"status":"live","auto":auto_enabled,"url":"https://mamdouh-bot.onrender.com"})

@app.route("/setwebhook")
def sethook():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://mamdouh-bot.onrender.com/webhook").json()
    return jsonify(r)

@app.route("/webhook", methods=["POST"])
def webhook():
    global auto_enabled
    try:
        j = request.get_json()
        if not j or "message" not in j: return "ok",200
        chat_id = j["message"]["chat"]["id"]
        text = j["message"].get("text","").lower()
        print(f"Telegram msg: {text} from {chat_id}", flush=True)
        if "/auto on" in text:
            auto_enabled=True
            send_text(chat_id,"🚀 الإمبراطورية مفعلة!")
        elif "/auto off" in text:
            auto_enabled=False
            send_text(chat_id,"⏸️ تم الإيقاف")
        elif "/post" in text:
            send_text(chat_id,"⏳ بنشر في البوت + الجروب + Pinterest...")
            threading.Thread(target=run_post, args=(chat_id,), daemon=True).start()
        elif "/status" in text:
            send_text(chat_id,f"📊 {'مفعل ✅' if auto_enabled else 'متوقف ❌'}\nالبوت: @مامدوح\nPinterest: {'مربوط' if PINTEREST_EMAIL else 'غير مربوط'}")
    except Exception as e:
        print(f"Webhook err: {e}", flush=True)
    return "ok",200
