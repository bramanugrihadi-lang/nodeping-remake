import asyncio
from typing import Optional
import httpx
from app.config import settings
from app.database import get_db
import aiosqlite


class TelegramNotifier:
    """Telegram bot notifier for alerts."""
    
    def __init__(self):
        self.token = settings.TELEGRAM_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.token}"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def _send_request(self, method: str, endpoint: str, **kwargs):
        """Send request to Telegram Bot API."""
        if not self.token or not self.chat_id:
            return None
        
        url = f"{self.api_base}/{endpoint}"
        try:
            response = await self.client.post(url, **kwargs)
            return response.json()
        except Exception as e:
            print(f"Telegram API error: {e}")
            return None
    
    async def send_alert(self, target_name: str, loss: float, latency: float) -> Optional[dict]:
        """Send alert message with ACK button."""
        if not self.token or not self.chat_id:
            return None
        
        message = (
            f"⚠️ *NODEPING ALERT*\n\n"
            f"*Target:* {target_name}\n"
            f"*Loss:* {loss:.1f}%\n"
            f"*Latency:* {latency:.1f}ms\n"
            f"*Time:* {asyncio.get_event_loop().time()}\n"
        )
        
        # ACK button inline keyboard
        import json
        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "Acknowledge",
                    "callback_data": f"ACK_{target_name}"
                }
            ]]
        }
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(keyboard)
        }
        
        return await self._send_request("POST", "sendMessage", data=payload)
    
    async def send_pdf(self, chat_id: str, file_path: str) -> Optional[dict]:
        """Send PDF document via Telegram."""
        if not self.token or not chat_id:
            return None
        
        try:
            with open(file_path, "rb") as f:
                files = {"document": f}
                payload = {"chat_id": chat_id, "caption": "PDF Report"}
                return await self._send_request("POST", "sendDocument", data=payload, files=files)
        except Exception as e:
            print(f"Error sending PDF: {e}")
            return None
    
    async def acknowledge_alert(self, target_name: str) -> bool:
        """Mark alert as acknowledged in DB."""
        async for db in get_db():
            try:
                await db.execute(
                    """UPDATE alerts SET acknowledged = 1 
                       WHERE target_name = ? AND acknowledged = 0 
                       ORDER BY timestamp DESC LIMIT 1""",
                    (target_name,)
                )
                await db.commit()
                return True
            except Exception as e:
                print(f"Error acknowledging alert: {e}")
                return False
            finally:
                break
        return False


async def poll_updates():
    """Poll Telegram for ACK callback queries."""
    if not settings.TELEGRAM_TOKEN:
        return
    
    offset = 0
    while True:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{TelegramNotifier().api_base}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                data = response.json()
                
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        
                        # Check for callback query (ACK button)
                        callback = update.get("callback_query", {})
                        data = callback.get("data", "")
                        
                        if data.startswith("ACK_"):
                            target_name = data[4:]  # Remove "ACK_" prefix
                            notifier = TelegramNotifier()
                            await notifier.acknowledge_alert(target_name)
                            
                            # Answer callback
                            await client.post(
                                f"{TelegramNotifier().api_base}/answerCallbackQuery",
                                data={"callback_query_id": callback.get("id")}
                            )
            
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(10)


if __name__ == "__main__":
    # Test sending alert
    async def test():
        notifier = TelegramNotifier()
        result = await notifier.send_alert("test-target", 75.0, 45.5)
        print(f"Result: {result}")
    
    asyncio.run(test())
