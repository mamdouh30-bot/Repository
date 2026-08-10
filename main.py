import os, time, random, json, logging
from datetime import datetime
from threading import Thread
from io import BytesIO
import requests
from PIL import Image, ImageDraw
from PIL import ImageFont
import qrcode
from flask import Flask, jsonify

# ============ إعدادات Render - بتتقرأ تلقائي ============
FB_PAGE_ID = os.getenv("FB_PAGE_ID") or os.getenv("PAGE_ID") or "370386486169123"
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN") or os.getenv("PAGE_ACCESS_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_IDS = os.getenv("GROUP_IDS", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
app = Flask(__name__)
HISTORY_FILE = "/tmp/posted_history.json"

# ============ كل منتجاتك الـ 35 - كاملة ============
PRODUCTS = [
    {"id":"B0H98BH2MT","title":"AI Decision Making","sub":"Master Data-Driven Decisions & Predictive Intelligence","url":"https://www.amazon.co.uk/dp/B0H98BH2MT","cat":"AI Business","asin":"B0H98BH2MT"},
    {"id":"B0H98NZ1NS","title":"AI Leadership","sub":"Lead High-Performance Teams & Drive AI Transformation","url":"https://www.amazon.co.uk/dp/B0H98NZ1NS","cat":"AI Business","asin":"B0H98NZ1NS"},
    {"id":"B0H94R5L7F","title":"AI Business Strategy","sub":"Design, Execute, and Scale Winning Strategies with AI","url":"https://www.amazon.co.uk/dp/B0H94R5L7F","cat":"AI Business","asin":"B0H94R5L7F"},
    {"id":"B0H8Z39WVC","title":"AI Project Management","sub":"Plan, Execute, Monitor & Automate High-Impact Projects","url":"https://www.amazon.co.uk/dp/B0H8Z39WVC","cat":"AI Business","asin":"B0H8Z39WVC"},
    {"id":"B0H8XQMYLD","title":"AI Entrepreneurship","sub":"Build, Launch, Scale AI-Powered Businesses","url":"https://www.amazon.co.uk/dp/B0H8XQMYLD","cat":"AI Business","asin":"B0H8XQMYLD"},
    {"id":"B0H8QD8TGG","title":"AI FINANCE","sub":"Automate Financial Operations, Detect Fraud & Forecast","url":"https://www.amazon.co.uk/dp/B0H8QD8TGG","cat":"AI Business","asin":"B0H8QD8TGG"},
    {"id":"B0H8SWNSWW","title":"AI Human Resources","sub":"Recruit Smarter, Develop Talent & Automate HR","url":"https://www.amazon.co.uk/dp/B0H8SWNSWW","cat":"AI Business","asin":"B0H8SWNSWW"},
    {"id":"B0H8P7KJJX","title":"AI OPERATIONS","sub":"Optimize, Automate, Scale Business Operations","url":"https://www.amazon.co.uk/dp/B0H8P7KJJX","cat":"AI Business","asin":"B0H8P7KJJX"},
    {"id":"B0H8LW1LKX","title":"AI CUSTOMER SERVICE","sub":"Deliver Exceptional 24/7 Customer Experiences","url":"https://www.amazon.co.uk/dp/B0H8LW1LKX","cat":"AI Business","asin":"B0H8LW1LKX"},
    {"id":"B0H8HX9RRL","title":"AI AUTOMATION","sub":"Automate Business Processes & Eliminate Repetitive Work","url":"https://www.amazon.co.uk/dp/B0H8HX9RRL","cat":"AI Business","asin":"B0H8HX9RRL"},
    {"id":"B0H8FHN5WB","title":"AI SALES","sub":"Use AI to Find More Customers & Close More Deals","url":"https://www.amazon.co.uk/dp/B0H8FHN5WB","cat":"AI Business","asin":"B0H8FHN5WB"},
    {"id":"B0H8324FGM","title":"AI Agents for Business","sub":"Build Intelligent Assistants That Work 24/7","url":"https://www.amazon.co.uk/dp/B0H8324FGM","cat":"AI Business","asin":"B0H8324FGM"},
    {"id":"B0H7Z6QS6X","title":"AI Automation for Small Business","sub":"Streamline Operations, Reduce Costs & Scale","url":"https://www.amazon.co.uk/dp/B0H7Z6QS6X","cat":"AI Business","asin":"B0H7Z6QS6X"},
    {"id":"B0H7XFVFKV","title":"THE ULTIMATE AI PRODUCTIVITY HANDBOOK","sub":"Master Focus, Workflows & Deep Work","url":"https://www.amazon.co.uk/dp/B0H7XFVFKV","cat":"Productivity","asin":"B0H7XFVFKV"},
    {"id":"B0H7Q4L27H","title":"The AI Advantage Ultimate Guide","sub":"Master ChatGPT, Automation & Prompt Engineering","url":"https://www.amazon.co.uk/dp/B0H7Q4L27H","cat":"AI Business","asin":"B0H7Q4L27H"},
    {"id":"B0GYDN1RGV","title":"The AI Advantage Book 2","sub":"Master AI, ChatGPT, Business Growth & Future-Ready Skills","url":"https://www.amazon.co.uk/dp/B0GYDN1RGV","cat":"AI Business","asin":"B0GYDN1RGV"},
    {"id":"B0H7TB5VL5","title":"1000 AI Prompts for Business & Marketing","sub":"Ultimate Library for ChatGPT, Claude & Gemini","url":"https://www.amazon.co.uk/dp/B0H7TB5VL5","cat":"AI Business","asin":"B0H7TB5VL5"},
    {"id":"B0H7MXSQ14","title":"Personal Finance & Wealth Planner","sub":"Ultimate Money Management Workbook","url":"https://www.amazon.co.uk/dp/B0H7MXSQ14","cat":"Finance","asin":"B0H7MXSQ14"},
    {"id":"B0H7MF8GW2","title":"Homeowner's Master Record Book","sub":"Ultimate Home Management System","url":"https://www.amazon.co.uk/dp/B0H7MF8GW2","cat":"Home","asin":"B0H7MF8GW2"},
    {"id":"B0H7BXPL95","title":"Home Maintenance & Repair Planner","sub":"Complete Home Maintenance Logbook","url":"https://www.amazon.co.uk/dp/B0H7BXPL95","cat":"Home","asin":"B0H7BXPL95"},
    {"id":"B0H75MRNHP","title":"Ultimate Home Inventory & Emergency Planner","sub":"Organize Home, Protect Assets & Plan Emergencies","url":"https://www.amazon.co.uk/dp/B0H75MRNHP","cat":"Home","asin":"B0H75MRNHP"},
    {"id":"B0H9HVV2M5","title":"AI Digital Transformation","sub":"Transform Organizations & Modernize Business Models","url":"https://www.amazon.co.uk/dp/B0H9HVV2M5","cat":"AI Business","asin":"B0H9HVV2M5"},
    {"id":"B0HDJ34J2P","title":"Communication Mastery","sub":"Master Human Connection, Influence & Persuasion","url":"https://www.amazon.com/dp/B0HDJ34J2P","cat":"Soft Skills","asin":"B0HDJ34J2P"},
    {"id":"B0HD5K3LHV","title":"Deep Work Mastery","sub":"Master Focus & Eliminate Distractions","url":"https://www.amazon.com/dp/B0HD5K3LHV","cat":"Productivity","asin":"B0HD5K3LHV"},
    {"id":"B0HCLJKMCY","title":"Deep Work Best Work","sub":"Produce Your Best Work in World of Interruptions","url":"https://www.amazon.com/dp/B0HCLJKMCY","cat":"Productivity","asin":"B0HCLJKMCY"},
    {"id":"B0HBX2L5W9","title":"TIME MANAGEMENT","sub":"Master Productivity & Eliminate Procrastination","url":"https://www.amazon.com/dp/B0HBX2L5W9","cat":"Productivity","asin":"B0HBX2L5W9"},
    {"id":"B0HBR3VD9C","title":"LEADERSHIP","sub":"Master Modern Leadership & Inspire Teams","url":"https://www.amazon.com/dp/B0HBR3VD9C","cat":"Leadership","asin":"B0HBR3VD9C"},
    {"id":"B0HB4YZXTJ","title":"Negotiation Skills Mastery","sub":"Master Business Negotiation & Persuasion","url":"https://www.amazon.com/dp/B0HB4YZXTJ","cat":"Soft Skills","asin":"B0HB4YZXTJ"},
    {"id":"B0H9YKV56P","title":"Make Money with AI","sub":"Build AI-Powered Businesses & Multiple Income Streams","url":"https://www.amazon.com/dp/B0H9YKV56P","cat":"AI Business","asin":"B0H9YKV56P"},
    {"id":"B0H9VPG9FM","title":"Emotional Intelligence","sub":"Master Self-Awareness & Emotional Mastery","url":"https://www.amazon.com/dp/B0H9VPG9FM","cat":"Soft Skills","asin":"B0H9VPG9FM"},
    {"id":"B0H9YKV56P2","title":"How to Make $1,000,000 with AI","sub":"Build Scalable AI Businesses & Multiple Income Streams","url":"https://www.amazon.com/dp/B0H9YKV56P","cat":"AI Business","asin":"B0H9YKV56P"},
    {"id":"upwork-ai","title":"AI Workforce Service on Upwork","sub":"AI Agents + n8n + WhatsApp CRM + Automation","url":"https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261","cat":"Services","asin":"UPWORK"},
    {"id":"redbubble","title":"Mamdouh Art Store - Redbubble","sub":"Professional Print on Demand Designs","url":"https://mamdouh-bdran.redbubble.com","cat":"Design","asin":"REDBUBBLE"},
    {"id":"ballwool","title":"Ballwool Premium Product","sub":"Exclusive Design Collection","url":"https://ballwool.com/products/311540","cat":"Design","asin":"BALLWOOL"},
]

def load_history():
    try:
        with open(HISTORY_FILE,'r') as f: return json.load(f)
    except: return {}

def save_history(h):
    try:
        with open(HISTORY_FILE,'w') as f: json.dump(h,f)
    except Exception as e:
        logging.error(f"Save history failed: {e}")

def generate_ad(product):
    # لو عندك Groq هيكتب إعلان أقوى
    if GROQ_API_KEY:
        try:
            prompt = f"Write a short, professional, high-converting Facebook ad in English for a book titled '{product['title']}' - subtitle '{product['sub']}' - category {product['cat']}. Include 3 benefits, emojis, and hashtags. Keep under 500 characters."
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"},
                json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}]}, timeout=15)
            if r.status_code==200:
                text = r.json()['choices'][0]['message']['content']
                return text + f"\n\n🔗 {product['url']}\n#AI #Business #AmazonBooks"
        except Exception as e:
            logging.warning(f"Groq error: {e}")

    templates = [
        f"🚨 هل تعاني من {product['cat']}؟\n\n{product['title']}\n{product['sub']}\n\n✅ حلول عملية مجربة\n✅ توفير 15+ ساعة أسبوعيا\n✅ نتائج من أول أسبوع\n\n🔗 {product['url']}\n#AI #BusinessGrowth #WebCraftStudio",
        f"💡 تخيل مضاعفة إنتاجيتك!\n\n{product['title']}\n{product['sub']}\n\n🎯 ستحصل على:\n• أتمتة ذكية\n• قرارات أذكى بالبيانات\n• أنظمة تعمل 24/7\n\n👇 {product['url']}",
        f"🏆 من مؤلف سلسلة AI Advantage - 20+ كتاب\n\nاليوم: {product['title']}\n{product['sub']}\n\nصمم للمدراء ورواد الأعمال.\n\n📚 {product['url']}\n#AmazonBestseller",
        f"🔥 {product['title']}\n\n{product['sub']}\n\n⚡️ محدث 2025 + أمثلة عملية\n🛒 {product['url']}"
    ]
    return random.choice(templates)

def create_image(product):
    W,H = 1080,1080
    img = Image.new('RGB',(W,H),(5,15,35))
    draw = ImageDraw.Draw(img)
    for i in range(H):
        draw.line([(0,i),(W,i)], fill=(5+i//10, 15+i//12, 35+i//8))
    try:
        if product['asin'].startswith('B0'):
            url = f"https://images-na.ssl-images-amazon.com/images/P/{product['asin']}.01.L.jpg"
            data = requests.get(url, timeout=12).content
            cover = Image.open(BytesIO(data)).convert('RGB')
            cover = cover.resize((520,720))
            img.paste(cover, (280,70))
    except Exception as e:
        logging.warning(f"Cover failed {product['id']}: {e}")
    try:
        qr = qrcode.make(product['url']).resize((200,200))
        img.paste(qr, (440,830))
    except: pass
    try:
        draw.text((40,930), product['title'][:50], fill=(255,255,255))
        draw.text((40,960), f"{product['cat']} | WebCraft Studio", fill=(120,200,255))
        draw.text((40,990), "Scan QR to Buy on Amazon", fill=(200,200,200))
    except: pass
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=92)
    buf.seek(0)
    return buf

def post_facebook(text, buf):
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        logging.warning("FB token/page id missing")
        return False
    try:
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
        files = {'source': ('ad.jpg', buf, 'image/jpeg')}
        data = {'message': text, 'access_token': FB_PAGE_TOKEN}
        r = requests.post(url, files=files, data=data, timeout=30)
        logging.info(f"FB {r.status_code} - {r.text[:200]}")
        return r.status_code==200
    except Exception as e:
        logging.error(f"FB error: {e}")
        return False

def post_telegram(text, buf):
    if not BOT_TOKEN:
        logging.warning("BOT_TOKEN missing")
        return False
    chats=[]
    if CHANNEL_ID: chats.append(CHANNEL_ID)
    if GROUP_IDS: chats.extend([g.strip() for g in GROUP_IDS.split(',') if g.strip()])
    if not chats:
        logging.warning("No telegram chats configured")
        return False
    ok=False
    for chat in chats:
        try:
            buf.seek(0)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('ad.jpg', buf, 'image/jpeg')}
            data = {'chat_id': chat, 'caption': text[:1024]}
            r = requests.post(url, files=files, data=data, timeout=20)
            logging.info(f"TG {chat}: {r.status_code}")
            ok = ok or r.status_code==200
            time.sleep(2)
        except Exception as e:
            logging.error(f"TG {chat} error: {e}")
    return ok

def agent_loop():
    history = load_history()
    logging.info(f"🚀 وكيل Mamdouh بدأ - {len(PRODUCTS)} منتج - شغال 24/7 - FB:{FB_PAGE_ID}")
    while True:
        try:
            sorted_prods = sorted(PRODUCTS, key=lambda p: history.get(p['id'],{}).get('last','2000-01-01'))
            product = sorted_prods[0]
            logging.info(f"📢 حملة جديدة: {product['title']}")
            ad_text = generate_ad(product)
            img_buf = create_image(product)
            img_buf.seek(0)
            fb_ok = post_facebook(ad_text, img_buf)
            time.sleep(4)
            img_buf.seek(0)
            tg_ok = post_telegram(ad_text, img_buf)
            history[product['id']] = {"last": datetime.now().isoformat(), "fb":fb_ok, "tg":tg_ok}
            save_history(history)
            wait = random.randint(45,90)
            logging.info(f"✅ تم {product['id']} FB:{fb_ok} TG:{tg_ok} - انتظار {wait} دقيقة")
            time.sleep(wait*60)
        except Exception as e:
            logging.error(f"❌ خطأ لكن الوكيل مستمر: {e}", exc_info=True)
            time.sleep(60)

@app.route('/')
def home():
    h = load_history()
    return jsonify({"status":"Agent Running 24/7","products":len(PRODUCTS),"posted":len(h),"fb_page":FB_PAGE_ID,"last":list(h.keys())[-3:] if h else []})

@app.route('/health')
def health():
    return "OK", 200

@app.route('/post-now')
def post_now():
    # لعمل تيست سريع
    try:
        p = random.choice(PRODUCTS)
        txt = generate_ad(p)
        buf = create_image(p)
        return jsonify({"product":p['id'],"text":txt[:200]})
    except Exception as e:
        return jsonify({"error":str(e)}),500

# مهم جدا لـ gunicorn - يبدأ الوكيل أول ما الملف يتحمل
Thread(target=agent_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT",10000)))
