
import httpx, os, logging
logger = logging.getLogger("whatsapp")

async def send_whatsapp(to: str, text: str, token: str, phone_id: str):
    if not token or not phone_id:
        logger.warning(f"[SIM] WhatsApp to {to}: {text[:100]}")
        return True
    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:1000]}}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=10)
            logger.info(f"WhatsApp {to} -> {r.status_code}")
            return r.status_code == 200
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return False
