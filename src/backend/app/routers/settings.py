from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import TelegramSettings, TelegramSettingsResponse, MessageResponse
from app.auth import get_current_user, require_admin
from app.database import get_db
import aiosqlite

router = APIRouter(prefix="/api", tags=["settings"])


def mask_token(token: str) -> str:
    """Mask token showing only last 4 chars."""
    if not token or len(token) < 4:
        return "*" * 4
    return "*" * (len(token) - 4) + token[-4:]


@router.get("/settings/telegram", response_model=TelegramSettingsResponse)
async def get_telegram_settings(
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get Telegram settings (admin only)."""
    await require_admin(current_user)
    
    cursor = await db.execute(
        "SELECT key, value FROM settings WHERE key IN ('TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')"
    )
    rows = await cursor.fetchall()
    
    settings_dict = {row["key"]: row["value"] for row in rows}
    
    return TelegramSettingsResponse(
        token=mask_token(settings_dict.get("TELEGRAM_TOKEN", "")),
        chat_id=settings_dict.get("TELEGRAM_CHAT_ID", "")
    )


@router.post("/settings/telegram", response_model=MessageResponse)
async def update_telegram_settings(
    settings: TelegramSettings,
    db=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update Telegram settings (admin only)."""
    await require_admin(current_user)
    
    # Upsert settings
    await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("TELEGRAM_TOKEN", settings.token)
    )
    await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("TELEGRAM_CHAT_ID", settings.chat_id)
    )
    await db.commit()
    
    return MessageResponse(message="Telegram settings updated successfully")
