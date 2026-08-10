import os, time, random, json, logging, re
from datetime import datetime
from threading import Thread
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
import qrcode
from flask import Flask

# ============ الإعدادات من Render ============
FB_PAGE_ID = os.getenv("FB_PAGE_ID") or os.getenv("PAGE_ID") or "370386486169123"
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN") or os.getenv("PAGE_ACCESS_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN") # تليجرام
CHANNEL_ID = os.getenv("CHANNEL_ID") # قناة تليجرام
GROUP_IDS = os.getenv("GROUP_IDS", "") # ممكن يكون أكتر من جروب مفصول بفاصلة
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
HISTORY_FILE = "posted_history.json"

# ============ كل منتجاتك الـ 35 ============
PRODUCTS = [
    {"id":"ai-decision","title":"AI Decision Making","sub":"Master Data-Driven Decisions, Predictive Intelligence & Strategic Thinking","url":"https://www.amazon.co.uk/dp/B0H98BH2MT","cat":"AI Business","asin":"B0H98BH2MT"},
    {"id":"ai-leadership","title":"AI Leadership","sub":"Lead High-Performance Teams, Drive AI-Powered Transformation","url":"https://www.amazon.co.uk/dp/B0H98NZ1NS","cat":"AI Business","asin":"B0H98NZ1NS"},
    {"id":"ai-strategy","title":"AI Business Strategy","sub":"Design, Execute, and Scale Winning Strategies with AI","url":"https://www.amazon.co.uk/dp/B0H94R5L7F","cat":"AI Business","asin":"B0H94R5L7F"},
    {"id":"ai-pm","title":"AI Project Management","sub":"Plan, Execute, Monitor, Automate High-Impact Projects","url":"https://www.amazon.co.uk/dp/B0H8Z39WVC","cat":"AI Business","asin":"B0H8Z39WVC"},
    {"id":"ai-entre","title":"AI Entrepreneurship","sub":"Build, Launch, Scale AI-Powered Businesses","url":"https://www.amazon.co.uk/dp/B0H8XQMYLD","cat":"AI Business","asin":"B0H8XQMYLD"},
    {"id":"ai-finance","title":"AI FINANCE","sub":"Automate Financial Operations, Detect Fraud & Forecast","url":"https://www.amazon.co.uk/dp/B0H8QD8TGG","cat":"AI Business","asin":"B0H8QD8TGG"},
    {"id":"ai-hr","title":"AI Human Resources","sub":"Recruit Smarter, Develop Talent & Automate HR","url":"https://www.amazon.co.uk/dp/B0H8SWNSWW","cat":"AI Business","asin":"B0H8SWNSWW"},
    {"id":"ai-ops","title":"AI OPERATIONS","sub":"Optimize, Automate, Scale Operations with AI Agents","url":"https://www.amazon.co.uk/dp/B0H8P7KJJX","cat":"AI Business","asin":"B0H8P7KJJX"},
    {"id":"ai-customer","title":"AI CUSTOMER SERVICE","sub":"Deliver Exceptional 24/7 Customer Experiences","url":"https://www.amazon.co.uk/dp/B0H8LW1LKX","cat":"AI Business","asin":"B0H8LW1LKX"},
    {"id":"ai-auto","title":"AI AUTOMATION","sub":"Automate Business Processes & Reduce Costs","url":"https://www.amazon.co.uk/dp/B0H8HX9RRL","cat":"AI Business","asin":"B0H8HX9RRL"},
    {"id":"ai-sales","title":"AI SALES","sub":"Find More Customers, Close More Deals with AI","url":"https://www.amazon.co.uk/dp/B0H8FHN5WB","cat":"AI Business","asin":"B0H8FHN5WB"},
    {"id":"ai-agents","title":"AI Agents for Business","sub":"Build Intelligent Assistants That Work 24/7","url":"https://www.amazon.co.uk/dp/B0H8324FGM","cat":"AI Business","asin":"B0H8324FGM"},
    {"id":"ai-smallbiz","title":"AI Automation for Small Business","sub":"Streamline Operations, Reduce Costs, Boost Productivity","url":"https://www.amazon.co.uk/dp/B0H7Z6QS6X","cat":"AI Business","asin":"B0H7Z6QS6X"},
    {"id":"ai-productivity","title":"THE ULTIMATE AI PRODUCTIVITY HANDBOOK","sub":"Master Focus, Knowledge Management & Smart Workflows","url":"https://www.amazon.co.uk/dp/B0H7XFVFKV","cat":"Productivity","asin":"B0H7XFVFKV"},
    {"id":"ai-adv-3","title":"The AI Advantage - Ultimate Practical Guide","sub":"Master ChatGPT, Automation & Prompt Engineering","url":"https://www.amazon.co.uk/dp/B0H7Q4L27H","cat":"AI Business","asin":"B0H7Q4L27H"},
    {"id":"ai-adv-2","title":"The AI Advantage Book 2","sub":"Master AI, ChatGPT, Prompt Engineering & Business Growth","url":"https://www.amazon.co.uk/dp/B0GYDN1RGV","cat":"AI Business","asin":"B0GYDN1RGV"},
    {"id":"ai-prompts","title":"1000 AI Prompts for Business & Marketing","sub":"Ultimate Library for ChatGPT, Claude & Gemini","url":"https://www.amazon.co.uk/dp/B0H7TB5VL5","cat":"AI Business","asin":"B0H7TB5VL5"},
    {"id":"ai-digital","title":"AI Digital Transformation","sub":"Transform Organizations & Modernize Business Models","url":"https://www.amazon.co.uk/dp/B0H9HVV2M5","cat":"AI Business","asin":"B0H9HVV2M5"},
    {"id":"make-money-ai","title":"Make Money with AI","sub":"Build AI-Powered Businesses & Multiple Income Streams","url":"https://www.amazon.com/dp/B0H9YKV56P","cat":"AI Business","asin":"B0H9YKV56P"},
    {"id":"million-ai","title":"How to Make $1,000,000 with AI","sub":"Build Scalable AI Businesses","url":"https://www.amazon.com/dp/B0H9YKV56P","cat":"AI Business","asin":"B0H9YKV56P"},
    {"id":"finance-planner","title":"Personal Finance & Wealth Planner","sub":"Ultimate Money Management Workbook","url":"https://www.amazon.co.uk/dp/B0H7MXSQ14","cat":"Finance","asin":"B0H7MXSQ14"},
    {"id":"homeowner-record","title":"Homeowner's Master Record Book","sub":"Ultimate Home Management System","url":"https://www.amazon.co.uk/dp/B0H7MF8GW2","cat":"Home","asin":"B0H7MF8GW2"},
    {"id":"home-maint","title":"Home Maintenance & Repair Planner","sub":"Complete Logbook for Repairs & Checklists","url":"https://www.amazon.co.uk/dp/B0H7BXPL95","cat":"Home","asin":"B0H7BXPL95"},
    {"id":"home-emergency","title":"Ultimate Home Inventory & Emergency Planner","sub":"Organize Home & Protect Assets","url":"https://www.amazon.co.uk/dp/B0H75MRNHP","cat":"Home","asin":"B0H75MRNHP"},
    {"id":"communication","title":"Communication Mastery","sub":"Master Human Connection, Influence & Persuasion","url":"https://www.amazon.com/dp/B0HDJ34J2P","cat":"Soft Skills","asin":"B0HDJ34J2P"},
    {"id":"focus","title":"FOCUS","sub":"Master Attention & Achieve Peak Performance","url":"https://www.amazon.com/dp/B0H7MF8GW2","cat":"Productivity","asin":"B0H7MF8GW2"},
    {"id":"deep-work","title":"Deep Work","sub":"Master Focus & Produce Your Best Work","url":"https://www.amazon.com/dp/B0HCLJKMCY","cat":"Productivity","asin":"B0HCLJKMCY"},
    {"id":"time-mgmt","title":"TIME MANAGEMENT","sub":"Master Productivity & Eliminate Procrastination","url":"https://www.amazon.com/dp/B0HBX2L5W9","cat":"Productivity","asin":"B0HBX2L5W9"},
    {"id":"leadership","title":"LEADERSHIP","sub":"Master Modern Leadership & Inspire Teams","url":"https://www.amazon.com/dp/B0HBR3VD9C","cat":"Leadership","asin":"B0HBR3VD9C"},
    {"id":"negotiation","title":"Negotiation Skills Mastery","sub":"Master Business Negotiation & Persuasion","url":"https://www.amazon.com/dp/B0HB4YZXTJ","cat":"Soft Skills","asin":"B0HB4YZXTJ"},
    {"id":"emotional","title":"Emotional Intelligence","sub":"Master Self-Awareness & Emotional Mastery","url":"https://www.amazon.com/dp/B0H9VPG9FM","cat":"Soft Skills","asin":"B0H9VPG9FM"},
    # مشاريعك
    {"id":"upwork","title":"AI Workforce Service","sub":"Build AI Agents + n8n + WhatsApp CRM Automation","url":"https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261","cat":"Services","asin":"UPWORK"},
    {"id":"redbubble","title":"Mamdouh Art Store - Redbubble","sub":"Professional Print on Demand Designs","url":"https://mamdouh-bdran.redbubble.com","cat":"Design","asin":"REDBUBBLE"},
    {"id":"ballwool","title":"Ballwool Premium Collection","sub":"Exclusive Ballwool Product","url":"https://ballwool.com/products/311540?1p=1PBAB2BA","cat":"Design","asin":"BALLWOOL"},
]

def load_history():
    try:
        with open(HISTORY_FILE,'r') as f: return json.load(f)
    except: return {}

def save_history(h):
    with open(HISTORY_FILE,'w') as f: json.dump(h,f)

# ============ مولد نصوص احترافي بـ Groq ============
def generate_pro_ad(product):
    # 5 أنماط احترافية
    styles = {
        "problem": f"🚨 هل تخسر وقت ومال بسبب {product['cat']}؟\n\nكتاب {product['title']} سيغير قواعد اللعبة!\n{product['sub']}\n\n✅ حلول عملية مجربة\n✅ توفير 15+ ساعة أسبوعيا\n✅ نتائج من أول أسبوع\n\n🔗 اطلبه الآن: {product['url']}\n#AI #BusinessGrowth",
        "benefit": f"💡 تخيل مضاعفة إنتاجيتك 3 مرات!\n\n{product['title']}\n{product['sub']}\n\n🎯 ماذا ستتعلم؟\n• أتمتة ذكية للمهام المتكررة\n• اتخاذ قرارات أذكى بالبيانات\n• بناء أنظمة تعمل 24/7 بدونك\n\n👇 {product['url']}",
        "authority": f"🏆 من مؤلف سلسلة AI Advantage - 20+ كتاب الأكثر مبيعا\n\nاليوم: {product['title']}\n{product['sub']}\n\nصمم خصيصا للمدراء ورواد الأعمال الطموحين.\n\n📚 احصل على نسختك: {product['url']}\n#AmazonBestseller #WebCraftStudio",
        "cta": f"🔥 عرض حصري - {product['title']}\n\n{product['sub']}\n\n⚡️ لماذا الآن؟\n• محتوى محدث 2025\n• أمثلة عملية\n• قابل للتطبيق فورا\n\n🛒 أمازون: {product['url']}"
    }

    # لو عندك Groq API استخدمه لصياغة أفضل
    if GROQ_API_KEY:
        try:
            prompt = f"اكتب إعلان احترافي قصير لكتاب بعنوان {product['title']} - {product['sub']} - الرابط {product['url']} - بأسلوب تسويقي قوي مع إيموجي وهاشتاجات، باللغة الإنجليزية مع لمسة عربية بسيطة"
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model":"llama-3.1-70b-versatile","messages":[{"role":"user","content":prompt}]}, timeout=15)
            if r.status_code==200:
                return r.json()['choices'][0]['message']['content'] + f"\n\n{product['url']}"
        except Exception as e:
            logging.warning(f"Groq failed: {e}")

    return random.choice(list(styles.values()))

# ============ مصمم صور احترافي ============
def create_professional_image(product):
    W,H = 1080,1350 # مقاس انستا/فيسبوك احترافي
    # خلفية متدرجة احترافية
    img = Image.new('RGB',(W,H),(5,15,35))
    draw = ImageDraw.Draw(img)
    for i in range(H):
        r = int(5 + i*0.15); g = int(15 + i*0.08); b = int(35 + i*0.12)
        draw.line([(0,i),(W,i)], fill=(r,g,b))

    # حاول تجيب غلاف الكتاب من أمازون
    try:
        if product['asin'].startswith('B0'):
            cover_url = f"https://images-na.ssl-images-amazon.com/images/P/{product['asin']}.01.L.jpg"
            cover_data = requests.get(cover_url, timeout=10).content
            cover = Image.open(BytesIO(cover_data)).convert('RGB')
            cover = cover.resize((500,750))
            img.paste(cover, (290, 100))
    except: pass

    # QR Code
    qr = qrcode.make(product['url'])
    qr = qr.resize((220,220))
    img.paste(qr, (430, 900))

    # نصوص
    try:
        font1 = ImageFont.truetype("arial.ttf", 48)
        font2 = ImageFont.truetype("arial.ttf", 28)
    except:
        font1 = ImageFont.load_default()
        font2 = ImageFont.load_default()

    draw.text((50, 1150), product['title'][:45], fill=(255,255,255), font=font1)
    draw.text((50, 1220), f"{product['cat']} | WebCraft Studio", fill=(120,200,255), font=font2)
    draw.text((50, 1260), "Scan QR to Buy on Amazon", fill=(200,200,200), font=font2)

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=95)
    buf.seek(0)
    return buf

# ============ النشر ============
def post_facebook(text, img_buf):
    if not FB_PAGE_TOKEN:
        logging.warning("No FB token")
        return False
    try:
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
        files = {'source': ('ad.jpg', img_buf, 'image/jpeg')}
        data = {'message': text, 'access_token': FB_PAGE_TOKEN}
        r = requests.post(url, files=files, data=data, timeout=30)
        logging.info(f"FB posted: {r.status_code}")
        return r.status_code==200
    except Exception as e:
        logging.error(f"FB error: {e}")
        return False

def post_telegram(text, img_buf):
    if not BOT_TOKEN: return False
    targets = []
    if CHANNEL_ID: targets.append(CHANNEL_ID)
    if GROUP_IDS: targets.extend([g.strip() for g in GROUP_IDS.split(',') if g.strip()])

    ok=False
    for chat in targets:
        try:
            img_buf.seek(0)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files = {'photo': ('ad.jpg', img_buf, 'image/jpeg')}
            data = {'chat_id': chat, 'caption': text[:1024], 'parse_mode':'Markdown'}
            r = requests.post(url, files=files, data=data, timeout=20)
            logging.info(f"TG {chat}: {r.status_code}")
            ok = ok or r.status_code==200
            time.sleep(3)
        except Exception as e:
            logging.error(f"TG error {chat}: {e}")
    return ok

# ============ الحلقة التي لا تتوقف أبدا ============
def agent_loop():
    history = load_history()
    logging.info(f"🚀 وكيل Mamdouh بدأ - {len(PRODUCTS)} منتج - شغال 24/7")

    while True: # لا يتوقف أبدا
        try:
            # اختار أقدم منتج لم ينشر
            sorted_prods = sorted(PRODUCTS, key=lambda p: history.get(p['id'],{}).get('last','2000-01-01'))
            product = sorted_prods[0]

            logging.info(f"📢 يصمم حملة لـ: {product['title']}")

            ad_text = generate_pro_ad(product)
            img_buf = create_professional_image(product)

            # انشر
            img_buf.seek(0)
            fb = post_facebook(ad_text, img_buf)
            time.sleep(5)
            img_buf.seek(0)
            tg = post_telegram(ad_text, img_buf)

            # حدث التاريخ
            history[product['id']] = {"last": datetime.now().isoformat(), "fb":fb, "tg":tg}
            save_history(history)

            # انتظر 45-90 دقيقة (عشوائي) - شغال ليل نهار بدون توقف
            wait = random.randint(45,90)
            logging.info(f"✅ نشر {product['id']} - FB:{fb} TG:{tg} - نوم {wait} دقيقة")
            time.sleep(wait*60)

        except Exception as e:
            logging.error(f"❌ خطأ كبير لكن الوكيل لن يتوقف: {e}")
            time.sleep(60) # يرتاح دقيقة ويرجع يكمل

# ============ Health Check لـ Render ============
app = Flask(__name__)
@app.route('/')
def home(): return "Mamdouh Marketing Agent Running 24/7 - Products: 35"

if __name__ == "__main__":
    # شغل الويب سيرفر في ثريد منفصل
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT",10000))), daemon=True).start()
    # شغل الوكيل الأساسي (لا يتوقف)
    agent_loop()
