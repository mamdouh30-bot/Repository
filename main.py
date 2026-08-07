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
 "B0H7XFVFKV": "THE ULTIMATE AI PRODUCTIVITY HANDBOOK - Book 4",
 "B0H7Q4L27H": "The AI Advantage Guide - Book 3",
 "B0GYDN1RGV": "The AI Advantage Master - Book 2",
 "B0H7TB5VL5": "1000 AI Prompts for Business - Book 1",
 "B0H7MXSQ14": "Personal Finance & Wealth Planner",
 "B0H7MF8GW2": "Homeowner's Master Record Book",
 "B0H7BXPL95": "Home Maintenance & Repair Planner",
 "B0H75MRNHP": "Home Inventory & Emergency Planner"
}
UPWORK_LINK = "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261"

def get_daily_campaign():
    import random, datetime
    book_id = list(BOOKS.keys())[datetime.datetime.now().day % len(BOOKS)]
    return f"""🔥 كتاب اليوم: {BOOKS[book_id]}
📚 {BOOKS[book_id]}
👉 https://www.amazon.co.uk/dp/{book_id}

💼 ولو عايز تحول بيزنسك لـ Autopilot زي الكتب دي:
{UPWORK_LINK}
7 وكلاء AI بيردوا في 28 ثانية ويوفروا $12.3k/شهر"""
