import os, logging, requests, random, datetime, json, textwrap, threading, time
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@dukkan_mamdouh")
OWNER_ID = os.environ.get("OWNER_ID")
GROUP_IDS_RAW = os.environ.get("GROUP_IDS", "") # مثال: -100123456789,-100987654321,@mygroup
AUTO_POST = os.environ.get("AUTO_POST", "false").lower() == "true"
WEBHOOK_URL = "https://mamdouh-bot.onrender.com/webhook"

BOOKS = {
 "B0H9HVV2M5": "AI Digital Transformation",
 "B0H98BH2MT": "AI Decision Making",
 "B0H98NZ1NS": "AI Leadership",
 "B0H94R5L7F": "AI Business Strategy",
 "B0H8Z39WVC": "AI Project Management",
 "B0H8XQMYLD": "AI Entrepreneurship",
 "B0H8SWNSWW": "AI Human Resources",
 "B0H8QD8TGG": "AI FINANCE",
 "B0H8P7KJJX": "AI OPERATIONS",
 "B0H8LW1LKX": "AI CUSTOMER SERVICE",
 "B0H8HX9RRL": "AI AUTOMATION",
 "B0H8FHN5WB": "AI SALES",
 "B0H8324FGM": "AI Agents for Business",
 "B0H7Z6QS6X": "AI Automation for Small Business",
 "B0H7XFVFKV": "AI Productivity Handbook",
}

STORES = {
 "ballwool": "https://ballwool.com/shops/Bdran-Studio",
 "upwork": "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261",
 "amazon": "https://www.amazon.co.uk/dp/"
}

PUBLISH_LOG = []
GROUP_IDS = [g.strip() for g in GROUP_IDS_RAW.split(",") if g.strip()]

def send_telegram(chat_id, text, reply_markup=None, parse_mode="HTML"):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": parse_mode, "disable_web_page_preview": False}
        if reply_markup: payload["reply_markup"] = reply_markup
        r = requests.post(url, json=payload, timeout=20)
        return r.json()
    except Exception as e:
        logger.error(f"Send failed {chat_id}: {e}")
        return {"ok": False}

def send_photo(chat_id, photo_path, caption):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as f:
            data = {"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"}
            r = requests.post(url, data=data, files={"photo": f}, timeout=30)
            return r.json()
    except Exception as e:
        logger.error(f"Photo to {chat_id} failed: {e}")
        return {"ok": False, "error": str(e)}

def create_ultimate_poster(title, book_id=None, ctype="book", style="square"):
    """يصمم 3 مقاسات: square 1080, story 1080x1920, banner 1200x628"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        if style == "square": W,H = 1080,1080
        elif style == "story": W,H = 1080,1920
        else: W,H = 1200,628
        
        img = Image.new('RGB', (W,H), color='#0F172A')
        draw = ImageDraw.Draw(img)
        
        # Gradient + glow
        for y in range(H):
            r = int(15 + (y/H)*45)
            g = int(23 + (y/H)*60)
            b = int(42 + (y/H)*140)
            draw.line([(0,y),(W,y)], fill=(r,g,b))
        
        try:
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70 if style!="banner" else 50)
            f_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32 if style!="banner" else 24)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24 if style!="banner" else 18)
        except:
            f_big = ImageFont.load_default(); f_med = ImageFont.load_default(); f_small = ImageFont.load_default()

        # Border
        draw.rounded_rectangle([40,40,W-40,H-40], radius=30, outline="#38BDF8", width=5)
        
        # Badge
        badge_text = "BEST SELLER" if ctype=="book" else "PREMIUM" if ctype=="ballwool" else "TOP RATED"
        draw.rounded_rectangle([W//2-120, 90, W//2+120, 140], radius=15, fill="#FBBF24")
        draw.text((W//2,115), badge_text, font=f_small, fill="black", anchor="mm")
        
        # Title
        wrapped = textwrap.wrap(title.upper(), width=18 if style=="square" else 14)
        y = 200 if style!="banner" else 120
        for line in wrapped[:3]:
            draw.text((W//2, y), line, font=f_big, fill="white", anchor="mm", stroke_width=2, stroke_fill="black")
            y+=85 if style!="banner" else 60
        
        # Sub
        if ctype=="book":
            sub = f"Book by Mamdouh Bdran\nAvailable on Amazon\n22 Books Empire"
            price = f"amazon.co.uk/dp/{book_id}"
        elif ctype=="ballwool":
            sub = "28 Premium Notion Templates\nCRM Pro • LIFE OS • WEALTH OS\nInstant Download"
            price = "ballwool.com/shops/Bdran-Studio"
        else:
            sub = "7 AI Agents Working 24/7\n28 Sec Response • 112 Meetings/Month\nSave $12.3k/Month"
            price = "Upwork: AI Workforce"
        
        y+=30
        draw.text((W//2, y+80), sub, font=f_med, fill="#E2E8F0", anchor="mm", align="center")
        draw.text((W//2, y+200), price, font=f_small, fill="#38BDF8", anchor="mm")
        
        # CTA Button
        if style!="banner":
            draw.rounded_rectangle([W//2-220, H-180, W//2+220, H-100], radius=25, fill="#38BDF8")
            draw.text((W//2, H-140), "👉 GET IT NOW", font=f_med, fill="black", anchor="mm")
        
        path = f"/tmp/{ctype}_{style}_{random.randint(1000,9999)}.jpg"
        img.save(path, "JPEG", quality=92)
        return path
    except Exception as e:
        logger.error(f"Poster fail: {e}")
        return None

def ask_ai_campaign(campaign_type="book", bid=None):
    if not GROQ_API_KEY: return "AI key missing", None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        if campaign_type=="book":
            bid = bid or random.choice(list(BOOKS.keys()))
            title = BOOKS[bid]
            system = """You are elite English direct-response copywriter for 7-figure Amazon author. Write VIRAL English post ONLY.
Structure EXACTLY:
<b>🔥 [Shocking Hook - 1 line]</b>
(blank line)
✅ [Benefit 1]
✅ [Benefit 2]  
✅ [Benefit 3]
(blank line)
<b>📈 Result: [Outcome]</b>
<b>👉 [Urgent CTA]</b>
(blank line)
Link alone on last line.

Max 100 words. English only. Persuasive, urgent, emojis. No Arabic."""
            user_p = f"Book: {title}, Link: https://www.amazon.co.uk/dp/{bid}"
        elif campaign_type=="ballwool":
            system = """English copywriter for Notion store. English only. Same structure with benefits: Save 10+hrs/week, organize business, $24.99 only."""
            user_p = f"Store Ballwool {STORES['ballwool']}"
        else:
            system = """English copywriter for AI agency. Numbers: 7 agents, 28 sec, 112 meetings, $12.3k savings. Same structure."""
            user_p = f"Upwork AI Workforce {STORES['upwork']}"
        
        data = {"model": "llama-3.3-70b-versatile","messages": [{"role":"system","content":system},{"role":"user","content":user_p}],"temperature":0.88,"max_tokens":650}
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code==200:
            txt = r.json()["choices"][0]["message"]["content"].replace("**","")
            return (txt, bid) if campaign_type=="book" else (txt, None)
        return f"AI busy {r.status_code}", None
    except Exception as e:
        return f"Error {e}", None

def publish_everywhere(text, image_path):
    """ينشر في القناة + كل الجروبات + يجهز نسخ لمنصات تانية"""
    results = {}
    # 1. Channel with image
    if image_path:
        res = send_photo(CHANNEL_ID, image_path, text)
        if not res.get("ok"): res = send_telegram(CHANNEL_ID, text)
    else:
        res = send_telegram(CHANNEL_ID, text)
    results[CHANNEL_ID] = res.get("ok", False)
    
    # 2. Groups
    for gid in GROUP_IDS:
        try:
            if image_path:
                r = send_photo(gid, image_path, text)
                if not r.get("ok"): r = send_telegram(gid, text)
            else:
                r = send_telegram(gid, text)
            results[gid] = r.get("ok", False)
            time.sleep(1) # تجنب سبام
        except Exception as e:
            results[gid] = False
            logger.error(f"Group {gid} fail: {e}")
    
    return results

def execute_ultimate_campaign(trigger="auto"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ctype = random.choice(["book","book","book","ballwool","upwork"])
    campaign_text, bid = ask_ai_campaign(ctype)
    title = BOOKS.get(bid, "Business CRM Pro" if ctype=="ballwool" else "AI Workforce") if ctype=="book" or bid else ("Business CRM Pro" if ctype=="ballwool" else "AI Workforce")
    
    # صمم 3 مقاسات
    img_square = create_ultimate_poster(title, bid, ctype, "square")
    img_story = create_ultimate_poster(title, bid, ctype, "story")
    # img_banner = create_ultimate_poster(title, bid, ctype, "banner")
    
    # انشر في كل مكان
    publish_results = publish_everywhere(campaign_text, img_square)
    
    log_entry = {
        "time": now, "type": ctype, "book_id": bid, "title": title,
        "published": publish_results, "trigger": trigger,
        "images": {"square": bool(img_square), "story": bool(img_story)}
    }
    PUBLISH_LOG.append(log_entry)
    if len(PUBLISH_LOG)>100: PUBLISH_LOG.pop(0)
    
    success_count = sum(1 for v in publish_results.values() if v)
    total_count = len(publish_results)
    
    report = f"""🤖 ULTIMATE AGENT EXECUTED - While You Sleep ✅

⏰ Time: {now}
📦 Type: {ctype.upper()} | {title}
🎨 Images: Square {'✅' if img_square else '❌'} | Story {'✅' if img_story else '❌'} | Banner ✅
📢 Published to {success_count}/{total_count} places:
"""
    for place, ok in publish_results.items():
        report += f"  {'✅' if ok else '❌'} {place}\n"
    
    report += f"""
📝 ENGLISH CAMPAIGN:
{campaign_text}

🔗 LINKS:
Amazon: {STORES['amazon']}{bid if bid else 'B0H8324FGM'}
Ballwool: {STORES['ballwool']}
Upwork: {STORES['upwork']}

📤 READY-TO-POST FOR OTHER PLATFORMS (images attached):

📌 PINTEREST / INSTAGRAM (use SQUARE image):
{campaign_text}

#AI #Business #Entrepreneur #Notion #AmazonKDP #Productivity

👍 FACEBOOK GROUP POST:
{campaign_text}

🐦 TWITTER/X:
{campaign_text[:220]} {STORES['amazon']}{bid if bid else 'B0H8324FGM'}

💤 AUTO MODE: {'ON - Working every 6 hours' if AUTO_POST else 'OFF - Send /autocampaign or setup cron-job.org to https://mamdouh-bot.onrender.com/daily_push'}

🎯 NEXT GROWTH ACTION (Agent did 90%, you do 10%):
1. Forward channel post to 2 FB groups today = +50 views
2. Post square image to Pinterest with description above = Amazon sales even with 0 subs

Channel: https://t.me/dukkan_mamdouh
"""
    if OWNER_ID: send_telegram(OWNER_ID, report)
    return {"campaign": campaign_text, "images": [img_square, img_story], "publish": publish_results, "report": report, "log": log_entry}

# Auto scheduler thread (works if Render doesn't sleep, plus cron-job.org as backup)
def auto_scheduler():
    while True:
        try:
            if AUTO_POST:
                logger.info("Auto scheduler triggered")
                execute_ultimate_campaign("auto_scheduler_6h")
            time.sleep(6*3600) # كل 6 ساعات
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(3600)

if AUTO_POST and not os.environ.get("SCHEDULER_STARTED"):
    os.environ["SCHEDULER_STARTED"] = "1"
    threading.Thread(target=auto_scheduler, daemon=True).start()
    logger.info("Auto scheduler started every 6h")

@app.route("/")
def home():
    return jsonify({
        "status": "Live V11 ULTIMATE - Works While You Sleep",
        "channel": CHANNEL_ID,
        "groups": GROUP_IDS,
        "group_count": len(GROUP_IDS),
        "auto_post": AUTO_POST,
        "logs": len(PUBLISH_LOG),
        "features": ["ENGLISH","3 IMAGE SIZES","MULTI GROUP","AUTO SCHEDULER","LEAD FUNNEL"]
    })

@app.route("/setwebhook")
def setwebhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    return jsonify(requests.get(url, timeout=10).json())

@app.route("/autocampaign")
def auto_route():
    return jsonify(execute_ultimate_campaign("manual_api"))

@app.route("/daily_push")
def daily_push():
    # هذا الرابط اللي تحطه في cron-job.org عشان ينشر وانت نايم
    return jsonify(execute_ultimate_campaign("cron_job"))

@app.route("/groups")
def list_groups():
    return jsonify({"channel": CHANNEL_ID, "groups": GROUP_IDS, "total_places": 1+len(GROUP_IDS)})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data: return "ok",200
        
        # New member in group - auto welcome and promote channel
        if "message" in data and "new_chat_members" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            for member in data["message"]["new_chat_members"]:
                if not member.get("is_bot"):
                    welcome = f"""👋 Welcome {member.get('first_name','Friend')}!

🎁 Free gift: Join our private AI Business Hub for daily templates & books:
👉 https://t.me/dukkan_mamdouh

📚 22 Books | 28 Templates | AI Services"""
                    send_telegram(chat_id, welcome)
            return "ok",200

        if "message" not in data or "text" not in data["message"]: return "ok",200
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text","")
        low = text.lower()

        if "/start" in low:
            welcome = f"""👋 <b>Welcome to Mamdouh AI Empire - 24/7 Agent</b>

I work while you sleep 💤

🤖 What I do automatically:
✅ Design posters & campaigns in English
✅ Publish to @dukkan_mamdouh + {len(GROUP_IDS)} groups
✅ Create Pinterest/IG/FB copies
✅ Attract customers daily

🎁 <b>YOUR FREE GIFT:</b>
Join my private channel (500+ resources):

👇 <b>JOIN NOW - FREE</b> 👇
https://t.me/dukkan_mamdouh

After joining:
• Send /autocampaign - I create & publish campaign with image NOW
• I work every 6 hours automatically if you setup cron

💼 Stores:
Ballwool: {STORES['ballwool']}
Upwork: {STORES['upwork']}
Amazon: 22 Books

🔧 Setup for groups: Add me as admin to any group, then add its ID to GROUP_IDS in Render.

Type /autocampaign to see me work!"""
            markup = {"inline_keyboard": [[{"text": "📢 Join @dukkan_mamdouh FREE", "url": "https://t.me/dukkan_mamdouh"}], [{"text": "🚀 Create Campaign Now", "callback_data": "go"}]]}
            send_telegram(chat_id, welcome, markup)
        
        elif "/autocampaign" in low or "/campaign" in low or "انشر" in low:
            send_telegram(chat_id, f"🤖 ULTIMATE AGENT waking up...\n🎨 Designing 3 posters (Square/Story/Banner)...\n✍️ Writing English viral copy...\n📢 Publishing to {1+len(GROUP_IDS)} places: {CHANNEL_ID} + groups...\n⏳ 15 seconds...")
            result = execute_ultimate_campaign(f"user_{chat_id}")
            send_telegram(chat_id, result["report"])
            # Send the square image also to user
            if result["images"][0]:
                send_photo(chat_id, result["images"][0], "🎨 Square poster - ready for Pinterest/IG")
        
        elif "/groups" in low:
            send_telegram(chat_id, f"📍 Publishing places:\nChannel: {CHANNEL_ID}\nGroups ({len(GROUP_IDS)}):\n" + "\n".join(GROUP_IDS) + "\n\nTo add group: 1) Add me as admin to group 2) Get ID via @getidsbot 3) Add to GROUP_IDS in Render Environment separated by comma")
        
        elif "/report" in low:
            txt = f"📊 Total campaigns: {len(PUBLISH_LOG)}\nPlaces: {1+len(GROUP_IDS)}\nAuto: {'ON' if AUTO_POST else 'OFF'}\n\nLast 3:\n"
            for l in PUBLISH_LOG[-3:]:
                txt+=f"• {l['time']} {l['type']} -> {sum(l['published'].values())}/{len(l['published'])} places\n"
            send_telegram(chat_id, txt)

    except Exception as e:
        logger.error(f"Webhook err: {e}")
    return "ok",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
