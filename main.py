# V6 ULTIMATE EMPIRE - 4 Channels
STORES = {
 "amazon": {"count": 22, "link": "https://www.amazon.co.uk/s?k=Mamdouh+Bdran"},
 "upwork": {"link": "https://www.upwork.com/services/product/development-it-an-ai-workforce-with-ai-agents-n8n-automation-whatsapp-crm-integration-2083154276523185261", "price": "$599-$3499"},
 "ballwool": {
  "link": "https://ballwool.com/shops/Bdran-Studio",
  "products": 28,
  "top": ["Business CRM Pro ULTRA $24.99", "LIFE OS 2.0 $24.99", "WEALTH OS 35-in-1 $59.99", "Kindergarten Curriculum Empire $2.99"]
 },
 "redbubble": {"link": "https://mamdouh-bdran.redbubble.com", "type": "Print on Demand"}
}
# BOOKS نفس الـ dict اللي فات + 
BOOKS = {...22 كتاب زي قبل...}

# أضف الأوامر دي جوه webhook:
# if "/empire" in text: reply = f"🏛️ إمبراطوريتك 4 قنوات:\n📚 أمازون 22 كتاب\n💼 Upwork {STORES['upwork']['link']}\n🛍️ Ballwool 28 منتج {STORES['ballwool']['link']}\n🎨 Redbubble {STORES['redbubble']['link']}"
# if "/ballwool" in text: reply = f"🛍️ Bdran-Studio - 28 منتج:\n" + "\n".join(STORES['ballwool']['top']) + f"\n👉 {STORES['ballwool']['link']}"
