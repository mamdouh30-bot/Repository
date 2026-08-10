import os, time, random, json, logging
from datetime import datetime
from threading import Thread
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
import qrcode
from flask import Flask, jsonify

# إعدادات Render
FB_PAGE_ID = os.getenv("FB_PAGE_ID") or os.getenv("PAGE_ID") or "370386486169123"
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN") or os.getenv("PAGE_ACCESS_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
GROUP_IDS = os.getenv("GROUP_IDS", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
app = Flask(__name__)
HISTORY_FILE = "/tmp/posted_history.json"

PRODUCTS = [
    {"id":"B0H98BH2MT","title":"AI Decision Making","sub":"Master Data-Driven Decisions","url":"https://www.amazon.co.uk/dp/B0H98BH2MT","cat":"AI Business","asin":"B0H98BH2MT"},
    {"id":"B0H98NZ1NS","title":"AI Leadership","sub":"Lead High-Performance Teams","url":"https://www.amazon.co.uk/dp/B0H98NZ1NS","cat":"AI Business","asin":"B0H98NZ1NS"},
    {"id":"B0H94R5L7F","title":"AI Business Strategy","sub":"Design Winning Strategies with AI","url":"https://www.amazon.co.uk/dp/B0H94R5L7F","cat":"AI Business","asin":"B0H94R5L7F"},
    {"id":"B0H8Z39WVC","title":"AI Project Management","sub":"Plan, Execute, Monitor Projects","url":"https://www.amazon.co.uk/dp/B0H8Z39WVC","cat":"AI Business","asin":"B0H8Z39WVC"},
    {"id":"B0H8XQMYLD","title":"AI Entrepreneurship","sub":"Build AI-Powered Businesses","url":"https://www.amazon.co.uk/dp/B0H8XQMYLD","cat":"AI Business","asin":"B0H8XQMYLD"},
    {"id":"B0H8QD8TGG","title":"AI FINANCE","sub":"Automate Finance & Detect Fraud","url":"https://www.amazon.co.uk/dp/B0H8QD8TGG","cat":"AI Business","asin":"B0H8QD8TGG"},
    {"id":"B0H8SWNSWW","title":"AI Human Resources","sub":"Recruit Smarter with AI","url":"https://www.amazon.co.uk/dp/B0H8SWNSWW","cat":"AI Business","asin":"B0H8SWNSWW"},
    {"id":"B0H8P7KJJX","title":"AI OPERATIONS","sub":"Optimize Operations with AI","url":"https://www.amazon.co.uk/dp/B0H8P7KJJX","cat":"AI Business","asin":"B0H8P7KJJX"},
    {"id":"B0H8LW1LKX","title":"AI CUSTOMER SERVICE","sub":"24/7 Exceptional Experiences","url":"https://www.amazon.co.uk/dp/B0H8LW1LKX","cat":"AI Business","asin":"B0H8LW1LKX"},
    {"id":"B0H8HX9RRL","title":"AI AUTOMATION","sub":"Eliminate Repetitive Work","url":"https://www.amazon.co.uk/dp/B0H8HX9RRL","cat":"AI Business","asin":"B0H8HX9RRL"},
    {"id":"B0H8FHN5WB","title":"AI SALES","sub":"Close More Deals with AI","url":"https://www.amazon.co.uk/dp/B0H8FHN5WB","cat":"AI Business","asin":"B0H8FHN5WB"},
    {"id":"B0H8324FGM","title":"AI Agents for Business","sub":"Assistants That Work 24/7","url":"https://www.amazon.co.uk/dp/B0H8324FGM","cat":"AI Business","asin":"B0H8324FGM"},
    {"id":"B0H7Z6QS6X","title":"AI Automation for Small Business","sub":"Streamline & Reduce Costs","url":"https://www.amazon.co.uk/dp/B0H7Z6QS6X","cat":"AI Business","asin":"B0H7Z6QS6X"},
    {"id":"B0H7XFVFKV","title":"AI PRODUCTIVITY HANDBOOK","sub":"Master Focus & Workflows","url":"https://www.amazon.co.uk/dp/B0H7XFVFKV","cat":"Productivity","asin":"B0H7XFVFKV"},
    {"id":"B0H7Q4L27H","title":"The AI Advantage","sub":"Master ChatGPT & Automation","url":"https://www.amazon.co.uk/dp/B0H7Q4L27H","cat":"AI Business","asin":"B0H7Q4L27H"},
    {"id":"B0H7TB5VL5","title":"1000 AI Prompts","sub":"Library for ChatGPT & Claude","url":"https://www.amazon.co.uk/dp/B0H7TB5VL5","cat":"AI Business","asin":"B0H7TB5VL5"},
    {"id":"B0H9HVV2M5","title":"AI Digital Transformation","sub":"Transform Organizations","url":"https://www.amazon.co.uk/dp/B0H9HVV2M5","cat":"AI Business","asin":"B0H9HVV2M5"},
    {"id":"B0H9YKV56P","title":"Make Money with AI","sub":"Multiple Income Streams","url":"https://www.amazon.com/dp/B0H9YKV56P","cat":"AI Business","asin":"B0H9YKV56P"},
    {"id":"upwork","title":"AI Workforce + n8n + WhatsApp CRM","sub":"Upwork Service","url":"https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261","cat":"Services","asin":"UPWORK"},
    {"id":"redbubble","title":"Mamdouh Art Store","sub":"Redbubble Designs","url":"https://mamdouh-bdran.redbubble.com","cat":"Design","asin":"REDBUBBLE"},
    {"id":"ballwool","title":"Ballwool Premium","sub":"Exclusive Collection","url":"https://ballwool.com/products/311540","cat":"Design","asin":"BALLWOOL"},
]

def load_history():
    try:
        with open(HISTORY_FILE,'r') as f: return json.load(f)
    except: return {}
def save_history(h):
    try:
        with open(HISTORY_FILE,'w') as f: json.dump(h,f)
    except: pass

def generate_ad(p):
    if GROQ_API_KEY:
        try:
            prompt = f"Write short professional Facebook ad for book '{p['title']}' subtitle '{p['sub']}' category {p['cat']}. 3 benefits, emojis, hashtags. Under 400 chars."
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}]}, timeout=15)
            if r.status_code==200:
                return r.json()['choices'][0]['message']['content'] + f"\n\n{ p['url']}"
        except: pass
    templates = [
        f"🚀 {p['title']}\n{p['sub']}\n\n✅ حلول عملية\n✅ توفير 15 ساعة أسبوعيا\n\n{p['url']}\n#AI #Business",
        f"💡 {p['title']}\n{p['sub']}\n\n🎯 أتمتة ذكية + قرارات أذكى\n\n{p['url']}",
        f"🏆 {p['title']}\n{p['sub']}\n\n📚 من سلسلة AI Advantage\n{p['url']}"
    ]
    return random.choice(templates)

def create_image(p):
    W,H=1080,1080
    img=Image.new('RGB',(W,H),(5,15,35))
    draw=ImageDraw.Draw(img)
    for i in range(H):
        draw.line([(0,i),(W,i)], fill=(5+i//10,15+i//12,35+i//8))
    try:
        if p['asin'].startswith('B0'):
            data=requests.get(f"https://images-na.ssl-images-amazon.com/images/P/{p['asin']}.01.L.jpg", timeout=10).content
            cover=Image.open(BytesIO(data)).convert('RGB').resize((500,700))
            img.paste(cover,(290,70))
    except: pass
    try:
        qr=qrcode.make(p['url']).resize((200,200))
        img.paste(qr,(440,830))
    except: pass
    try:
        draw.text((40,930), p['title'][:48], fill=(255,255,255))
        draw.text((40,960), f"{p['cat']} | WebCraft Studio", fill=(120,200,255))
    except: pass
    buf=BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)
    return buf

def post_fb(text, buf):
    if not FB_PAGE_TOKEN: return False
    try:
        r=requests.post(f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos",
            files={'source':('ad.jpg',buf,'image/jpeg')},
            data={'message':text,'access_token':FB_PAGE_TOKEN}, timeout=30)
        logging.info(f"FB {r.status_code}")
        return r.status_code==200
    except Exception as e:
        logging.error(f"FB err {e}")
        return False

def post_tg(text, buf):
    if not BOT_TOKEN: return False
    chats=[]
    if CHANNEL_ID: chats.append(CHANNEL_ID)
    if GROUP_IDS: chats.extend([g.strip() for g in GROUP_IDS.split(',') if g.strip()])
    ok=False
    for chat in chats:
        try:
            buf.seek(0)
            r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                files={'photo':('ad.jpg',buf,'image/jpeg')},
                data={'chat_id':chat,'caption':text[:1024]}, timeout=20)
            logging.info(f"TG {chat} {r.status_code}")
            ok=ok or r.status_code==200
        except Exception as e:
            logging.error(f"TG err {e}")
    return ok

def agent_loop():
    history=load_history()
    logging.info(f"🚀 Agent Started - {len(PRODUCTS)} products - FB:{FB_PAGE_ID}")
    while True:
        try:
            prod=sorted(PRODUCTS, key=lambda p: history.get(p['id'],{}).get('last','2000-01-01'))[0]
            logging.info(f"Posting {prod['title']}")
            txt=generate_ad(prod)
            buf=create_image(prod)
            buf.seek(0)
            fb=post_fb(txt, buf)
            time.sleep(3)
            buf.seek(0)
            tg=post_tg(txt, buf)
            history[prod['id']]={"last":datetime.now().isoformat(),"fb":fb,"tg":tg}
            save_history(history)
            wait=random.randint(45,90)
            logging.info(f"Done {prod['id']} FB:{fb} TG:{tg} sleep {wait}m")
            time.sleep(wait*60)
        except Exception as e:
            logging.error(f"Loop error {e}", exc_info=True)
            time.sleep(60)

@app.route('/')
def home():
    h=load_history()
    return jsonify({"status":"Running 24/7","products":len(PRODUCTS),"posted":len(h),"fb_page":FB_PAGE_ID})

@app.route('/health')
def health():
    return "OK",200

Thread(target=agent_loop, daemon=True).start()

if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT",10000)))
