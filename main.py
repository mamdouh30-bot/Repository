import os, logging, requests, random, datetime
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://mamdouh-bot.onrender.com/webhook"

BOOKS = {
 "B0H9HVV2M5": "AI Digital Transformation - Book 18",
 "B0H98BH2MT": "AI Decision Making - Book 17",
 "B0H98NZ1NS": "AI Leadership - Book 16",
 "B0H94R5L7F": "AI Business Strategy - Book 15",
 "B0H8Z39WVC": "AI Project Management - Book 14",
 "B0H8XQMYLD": "AI Entrepreneurship - Book 13",
 "B0H8SWNSWW": "AI Human Resources - Book 12",
 "B0H8QD8TGG": "AI FINANCE - Book 11",
 "B0H8P7KJJX": "AI OPERATIONS - Book 10",
 "B0H8LW1LKX": "AI CUSTOMER SERVICE - Book 9",
 "B0H8HX9RRL": "AI AUTOMATION - Book 8",
 "B0H8FHN5WB": "AI SALES - Book 7",
 "B0H8324FGM": "AI Agents for Business - Book 6",
 "B0H7Z6QS6X": "AI Automation for Small Business - Book 5",
 "B0H7XFVFKV": "ULTIMATE AI PRODUCTIVITY HANDBOOK - Book 4",
 "B0H7Q4L27H": "The AI Advantage Guide - Book 3",
 "B0GYDN1RGV": "The AI Advantage Master - Book 2",
 "B0H7TB5VL5": "1000 AI Prompts for Business - Book 1",
 "B0H7MXSQ14": "Personal Finance Planner",
 "B0H7MF8GW2": "Homeowner Master Record Book",
 "B0H7BXPL95": "Home Maintenance Planner",
 "B0H75MRNHP": "Home Inventory Planner"
}

STORES = {
 "ballwool": "https://ballwool.com/shops/Bdran-Studio",
 "redbubble": "https://mamdouh-bdran.redbubble.com",
 "upwork": "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261"
}

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text[:4000], "parse_mode": "Markdown"}
        return requests.post(url, json=payload, timeout=15).ok
    except: return False

def ask_ai(user_text):
    if not GROQ_API_KEY: return "GROQ key missing"
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        system = f"You are Mamdouh AI Marketing Agent. You have 22 Amazon books, 28 Ballwool products at {STORES['ballwool']}, Redbubble {STORES['redbubble']}, Upwork {STORES['upwork']}. Answer in Egyptian Arabic and promote them."
        data = {"model": "llama-3.3-70b-versatile","messages": [{"role":"system","content":system},{"role":"user","content":user_text}],"temperature":0.7,"max_tokens":1000}
        r = requests.post(url, headers=headers, json=data, timeout=25)
        if r.status_code==200: return r.json()["choices"][0]["message"]["content"]
        return f"AI busy {r.status_code}"
    except Exception as e: return f"Error: {e}"

@app.route("/")
def home(): return jsonify({"status":"Live V6 Empire","books":len(BOOKS),"stores":STORES,"groq":bool(GROQ_API_KEY)})

@app.route("/setwebhook")
def set_webhook_route():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}"
    return jsonify(requests.get(url, timeout=10).json())

@app.route("/books")
def list_books(): return jsonify(BOOKS)

@app.route("/empire")
def empire(): return jsonify({"channels":4,"amazon_books":22,"ballwool_products":28,"stores":STORES})

@app.route("/campaign")
def campaign():
    bid = random.choice(list(BOOKS.keys()))
    txt = ask_ai(f"اعمل حملة تسويقية قصيرة لكتاب {BOOKS[bid]} https://www.amazon.co.uk/dp/{bid}")
    return jsonify({"book":bid,"campaign":txt})

@app.route("/daily_push")
def daily_push():
    bid = list(BOOKS.keys())[datetime.datetime.now().day % len(BOOKS)]
    txt = f"📚 كتاب اليوم: {BOOKS[bid]}\n👉 https://www.amazon.co.uk/dp/{bid}\n\n🛍️ متجري Ball
