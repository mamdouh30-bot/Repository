import os, logging, requests, random, datetime, json, textwrap, threading, time
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

# --- ENV ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@dukkan_mamdouh")
OWNER_ID = os.environ.get("OWNER_ID")
GROUP_IDS_RAW = os.environ.get("GROUP_IDS", "")
AUTO_POST = os.environ.get("AUTO_POST", "false").lower() == "true"
WEBHOOK_URL = "https://mamdouh-bot.onrender.com/webhook"
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL", "") # حط هنا رابط Make.com

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
 "amazon_base": "https://www.amazon.co.uk/dp/"
}

PUBLISH_LOG = []
LEADS_LOG = []
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
        return {"ok": False}

def groq_chat(system_prompt, user_prompt, temp=0.8, max_tokens=600):
    if not GROQ_API_KEY: return "AI key missing"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {"model": "llama-3.3-70b-versatile","messages": [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],"temperature":temp,"max_tokens":max_tokens}
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code==200:
            return r.json()["choices"][0]["message"]["content"].replace("**","")
        return f"AI busy {r.status_code}"
    except Exception as e:
        return f"Error {e}"

# --- 1. ANALYST BRAIN: يختار افضل حملة بناء على الوقت والاداء ---
def choose_best_campaign():
    # تحليل بسيط: الصباح كتب، الظهر Ballwool، المساء Upwork
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12: return "book"
    if 12 <= hour < 18: return "ballwool"
    return "upwork" # المساء خدمات غالية

# --- 2. DESIGNER + COPYWRITER ---
def create_ultimate_poster(title, book_id=None, ctype="book", style="square"):
    try:
        from PIL import Image, ImageDraw, ImageFont
        if style == "square": W,H = 1080,1080
        elif style == "story": W,H = 1080,1920
        else: W,H = 1200,628
        img = Image.new('RGB', (W,H), color='#0F172A')
        draw = ImageDraw.Draw(img)
        for y in range(H):
            r = int(15 + (y/H)*45); g = int(23 + (y/H)*60); b = int(42 + (y/H)*140)
            draw.line([(0,y),(W,y)], fill=(r,g,b))
        try:
            f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70 if style!="banner" else 50)
            f_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32 if style!="banner" else 24)
            f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24 if style!="banner" else 18)
        except:
            f_big = ImageFont.load_default(); f_med = ImageFont.load_default(); f_small = ImageFont.load_default()
        draw.rounded_rectangle([40,40,W-40,H-40], radius=30, outline="#38BDF8", width=5)
        badge_text = "BEST SELLER" if ctype=="book" else "PREMIUM" if ctype=="ballwool" else "TOP RATED"
        draw.rounded_rectangle([W//2-120, 90, W//2+120, 140], radius=15, fill="#FBBF24")
        draw.text((W//2,115), badge_text, font=f_small, fill="black", anchor="mm")
        wrapped = textwrap.wrap(title.upper(), width=18 if style=="square" else 14)
        y = 200 if style!="banner" else 120
        for line in wrapped[:3]:
            draw.text((W//2, y), line, font=f_big, fill="white", anchor="mm", stroke_width=2, stroke_fill="black")
            y+=85 if style!="banner" else 60
        if ctype=="book":
            sub = f"Book by Mamdouh Bdran\n22 Books Empire\nAvailable on Amazon"
            price = f"amazon.co.uk/dp/{book_id}"
        elif ctype=="ballwool":
            sub = "28 Premium Notion Templates\nCRM Pro • LIFE OS • WEALTH OS"
            price = "ballwool.com/shops/Bdran-Studio"
        else:
            sub = "7 AI Agents Working 24/7\n28 Sec Response • 112 Meetings/Month"
            price = "Upwork: AI Workforce"
        y+=30
        draw.text((W//2, y+80), sub, font=f_med, fill="#E2E8F0", anchor="mm", align="center")
        draw.text((W//2, y+200), price, font=f_small, fill="#38BDF8", anchor="mm")
        if style!="banner":
            draw.rounded_rectangle([W//2-220, H-180, W//2+220, H-100], radius=25, fill="#38BDF8")
            draw.text((W//2, H-140), "GET IT NOW", font=f_med, fill="black", anchor="mm")
        path = f"/tmp/{ctype}_{style}_{random.randint(1000,9999)}.jpg"
        img.save(path, "JPEG", quality=92)
        return path
    except Exception as e:
        logger.error(f"Poster fail: {e}")
        return None

def ask_ai_campaign(campaign_type="book", bid=None):
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
Max 100 words. English only. Persuasive, urgent, emojis."""
        user_p = f"Book: {title}, Link: https://www.amazon.co.uk/dp/{bid}?utm_source=telegram&utm_campaign={campaign_type}"
        txt = groq_chat(system, user_p, 0.88, 650)
        return txt, bid
    elif campaign_type=="ballwool":
        system = """English copywriter for Notion store. Same structure. Benefits: Save 10+hrs/week, organize business, $24.99 only. Link ballwool.com"""
        user_p = f"Store Ballwool {STORES['ballwool']}"
        txt = groq_chat(system, user_p, 0.85, 600)
        return txt, None
    else:
        system = """English copywriter for AI agency. Numbers: 7 agents, 28 sec, 112 meetings, $12.3k savings. Same structure."""
        user_p = f"Upwork AI Workforce {STORES['upwork']}"
        txt = groq_chat(system, user_p, 0.85, 600)
        return txt, None

# --- 3. PUBLISHER ---
def publish_everywhere(text, image_path):
    results = {}
    # Channel
    if image_path:
        res = send_photo(CHANNEL_ID, image_path, text)
        if not res.get("ok"): res = send_telegram(CHANNEL_ID, text)
    else:
        res = send_telegram(CHANNEL_ID, text)
    results[CHANNEL_ID] = res.get("ok", False)
    # Groups
    for gid in GROUP_IDS:
        try:
            if image_path:
                r = send_photo(gid, image_path, text)
                if not r.get("ok"): r = send_telegram(gid, text)
            else:
                r = send_telegram(gid, text)
            results[gid] = r.get("ok", False)
            time.sleep(5) # مهم جدا ضد السبام
        except Exception as e:
            results[gid] = False
            logger.error(f"Group {gid} fail: {e}")
    # Make.com webhook for other platforms
    if MAKE_WEBHOOK_URL and image_path:
        try:
            requests.post(MAKE_WEBHOOK_URL, json={"text": text, "image_path": image_path, "channel": CHANNEL_ID}, timeout=10)
            results["make.com"] = True
        except:
            results["make.com"] = False
    return results

# --- 4. SALES AGENT: يرد على العملاء ---
def handle_customer_ai(user_text, user_name="Friend"):
    system = f"""You are professional Sales & Support Agent for Mamdouh Bdran.
You have 3 product lines:
1. 22 Amazon Books: {list(BOOKS.values())[:5]}... Base link {STORES['amazon_base']}
2. Ballwool Store: 28 Notion Templates (CRM Pro, LIFE OS, WEALTH OS) at $24.99 - {STORES['ballwool']}
3. Upwork Service: AI Workforce - 7 AI agents automate business - {STORES['upwork']}

Your job:
- Reply in same language as user (Arabic if Arabic, English if English)
- Be friendly, short (max 80 words), helpful, sales-oriented but not pushy
- If user asks about a topic, recommend the most relevant book/template/service with link
- If user wants to buy, give direct link and say owner will contact them
- Always end with a CTA question

User name: {user_name}
"""
    reply = groq_chat(system, user_text, 0.7, 350)
    # Detect hot lead
    hot_keywords = ["buy","price","how much","link","interested","purchase","want","شراء","مهتم","سعر","كام","اشتري","تفاصيل"]
    is_hot = any(k in user_text.lower() for k in hot_keywords)
    return reply, is_hot

def execute_ultimate_campaign(trigger="auto"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ctype = choose_best_campaign() # Analyst Brain
    campaign_text, bid = ask_ai_campaign(ctype) # Copywriter
    title = BOOKS.get(bid, "Business CRM Pro" if ctype=="ballwool" else "AI Workforce")
    img_square = create_ultimate_poster(title, bid, ctype, "square") # Designer
    img_story = create_ultimate_poster(title, bid, ctype, "story")
    publish_results = publish_everywhere(campaign_text, img_square) # Publisher
    log_entry = {"time": now, "type": ctype, "book_id": bid, "title": title, "published": publish_results, "trigger": trigger}
    PUBLISH_LOG.append(log_entry)
    if len(PUBLISH_LOG)>100: PUBLISH_LOG.pop(0)
    success_count = sum(1 for v in publish_results.values() if v)
    total_count = len(publish_results)
    report = f"🤖 AGENCY EXECUTED ✅\n\n⏰ {now}\n🧠 Analyst chose: {ctype.upper()} ({title})\n🎨 Design: Square {'✅' if img_square else '❌'} | Story {'✅' if img_story else '❌'}\n📢 Publisher: {success_count}/{total_count} places\n\n📝 Campaign:\n{campaign_text}\n\n🔗 Amazon: {STORES['amazon_base']}{bid if bid else 'B0H8324FGM'}\nBallwool: {STORES['ballwool']}\nUpwork: {STORES['upwork']}\n\n💤 Auto: {'ON' if AUTO_POST else 'OFF'} | Leads: {len(LEADS_LOG)}"
    if OWNER_ID: send_telegram(OWNER_ID, report)
    return {"campaign": campaign_text, "publish": publish_results, "report": report}

def auto_scheduler():
    while True:
        try:
            if AUTO_POST:
                logger.info("Auto scheduler triggered")
                execute_ultimate_campaign("auto_scheduler_6h")
            time.sleep(6*3600)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(3600)

if AUTO_POST and not os.environ.get("SCHEDULER_STARTED"):
    os.environ["SCHEDULER_STARTED"] = "1"
    threading.Thread(target=auto_scheduler, daemon=True).start()

@app.route("/")
def home():
    return jsonify({"status": "V12 AGENCY - Full Marketing Agency","channel": CHANNEL_ID,"groups": GROUP_IDS,"auto_post": AUTO_POST,"campaigns": len(PUBLISH_LOG),"leads": len(LEADS_LOG)})

@app.route("/setwebhook")
def setwebhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    return jsonify(requests.get(url, timeout=10).json())

@app.route("/autocampaign")
def auto_route():
    return jsonify(execute_ultimate_campaign("manual_api"))

@app.route("/daily_push")
def daily_push():
    return jsonify(execute_ultimate_campaign("cron_job"))

@app.route("/groups")
def list_groups():
    return jsonify({"channel": CHANNEL_ID, "groups": GROUP_IDS, "total": 1+len(GROUP_IDS)})

@app.route("/leads")
def list_leads():
    return jsonify({"total": len(LEADS_LOG), "leads": LEADS_LOG[-20:]})

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data: return "ok",200
        if "message" in data and "new_chat_members" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            for member in data["message"]["new_chat_members"]:
                if not member.get("is_bot"):
                    welcome = f"👋 Welcome {member.get('first_name','Friend')}!\n\n🎁 Free gift: Join our private AI Business Hub:\n👉 https://t.me/dukkan_mamdouh\n\n📚 22 Books | 28 Templates | AI Services"
                    send_telegram(chat_id, welcome)
            return "ok",200
        if "message" not in data or "text" not in data["message"]: return "ok",200
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text","")
        low = text.lower()
        chat_type = msg["chat"].get("type","private")
        first_name = msg.get("from",{}).get("first_name","Friend")

        if low.startswith("/id"):
            send_telegram(chat_id, f"🆔 <code>{chat_id}</code>\nType: {chat_type}\nTitle: {msg['chat'].get('title','Private')}", parse_mode="HTML")
            return "ok",200

        if "/start" in low:
            welcome = f"👋 <b>Welcome to Mamdouh AI Agency - 24/7</b>\n\nI am your full marketing team 💼\n\n🤖 My 5 roles:\n1. 🧠 Analyst - chooses best product to sell\n2. 🎨 Designer - creates posters\n3. 📢 Publisher - posts to {1+len(GROUP_IDS)} places + social media\n4. 💬 Sales Agent - I reply to customers instantly\n5. 📊 Analytics - tracks everything\n\n🎁 Join: https://t.me/dukkan_mamdouh\n\nCommands:\n/autocampaign - run campaign now\n/groups - list places\n/leads - show leads\n/report - analytics\n/id - get chat ID"
            markup = {"inline_keyboard": [[{"text": "📢 Join @dukkan_mamdouh FREE", "url": "https://t.me/dukkan_mamdouh"}], [{"text": "🚀 Run Campaign Now", "callback_data": "go"}]]}
            send_telegram(chat_id, welcome, markup)
            return "ok",200

        if "/autocampaign" in low or "/campaign" in low:
            send_telegram(chat_id, f"🤖 AGENCY waking up...\n🧠 Analyst choosing...\n🎨 Designing...\n📢 Publishing to {1+len(GROUP_IDS)} places...")
            result = execute_ultimate_campaign(f"user_{chat_id}")
            send_telegram(chat_id, result["report"])
            return "ok",200

        if "/groups" in low:
            send_telegram(chat_id, f"📍 Places:\nChannel: {CHANNEL_ID}\nGroups ({len(GROUP_IDS)}):\n" + "\n".join(GROUP_IDS))
            return "ok",200

        if "/report" in low or "/analyze" in low:
            txt = f"📊 AGENCY ANALYTICS\nCampaigns: {len(PUBLISH_LOG)}\nLeads: {len(LEADS_LOG)}\nPlaces: {1+len(GROUP_IDS)}\nAuto: {'ON' if AUTO_POST else 'OFF'}\n\nLast 3:\n"
            for l in PUBLISH_LOG[-3:]:
                txt+=f"• {l['time']} {l['type']} -> {sum(l['published'].values())}/{len(l['published'])}\n"
            if LEADS_LOG:
                txt+=f"\n🔥 Last leads:\n" + "\n".join([f"{l['name']}: {l['text'][:40]}" for l in LEADS_LOG[-3:]])
            send_telegram(chat_id, txt)
            return "ok",200

        if "/leads" in low:
            if not LEADS_LOG:
                send_telegram(chat_id, "No leads yet. Sales Agent is waiting...")
            else:
                txt = f"💼 LEADS ({len(LEADS_LOG)}):\n"
                for l in LEADS_LOG[-10:]:
                    txt+=f"\n👤 {l['name']} ({l['chat_id']})\n{l['text'][:80]}\nTime: {l['time']} {'🔥HOT' if l['hot'] else ''}\n"
                send_telegram(chat_id, txt)
            return "ok",200

        # --- SALES AGENT: رد تلقائي على العملاء في الخاص ---
        if chat_type == "private":
            # تجاهل الاوامر
            if text.startswith("/"): return "ok",200
            reply, is_hot = handle_customer_ai(text, first_name)
            send_telegram(chat_id, reply)
            # حفظ الليد
            lead = {"chat_id": chat_id, "name": first_name, "text": text, "reply": reply, "hot": is_hot, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
            LEADS_LOG.append(lead)
            if len(LEADS_LOG)>200: LEADS_LOG.pop(0)
            if is_hot and OWNER_ID:
                send_telegram(OWNER_ID, f"🔥 HOT LEAD!\n👤 {first_name} (ID:{chat_id})\n💬 Said: {text}\n🤖 Replied: {reply}\n\nGo close the deal!")
            return "ok",200

    except Exception as e:
        logger.error(f"Webhook err: {e}")
    return "ok",200

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
