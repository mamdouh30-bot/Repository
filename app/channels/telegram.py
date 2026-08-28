
import httpx, logging
logger = logging.getLogger("telegram")

async def send_telegram(chat_id: str, text: str, token: str):
    if not token:
        logger.warning(f"[SIM] Telegram to {chat_id}: {text[:100]}")
        return True
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, timeout=10)
            return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False
