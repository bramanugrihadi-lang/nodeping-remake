from fastapi import APIRouter, Depends
from app.database import get_db

router = APIRouter(prefix="/api", tags=["sync"])


@router.get("/sync-status")
async def sync_status(db=Depends(get_db)):
    """Get real-time sync status for dashboard."""
    from app.schemas import Target
    
    cursor = await db.execute("SELECT * FROM targets ORDER BY id")
    targets = await cursor.fetchall()
    
    target_list = [
        Target(
            id=row["id"],
            name=row["name"],
            ip=row["ip"],
            interval=row["interval"],
            ping_count=row["ping_count"],
            last_loss=row["last_loss"],
            is_online=bool(row["is_online"])
        )
        for row in targets
    ]
    
    online = sum(1 for t in target_list if t.is_online)
    offline = len(target_list) - online
    avg_latency = sum(t.last_loss for t in target_list) / len(target_list) if target_list else 0
    
    return {
        "targets": target_list,
        "summary": {
            "total": len(target_list),
            "online": online,
            "offline": offline,
            "avg_latency": round(avg_latency, 2)
        }
    }
