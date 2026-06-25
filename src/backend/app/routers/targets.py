from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import Target, TargetCreate, TargetUpdate, MessageResponse
from app.auth import get_current_user, require_admin
from app.database import get_db
import aiosqlite

router = APIRouter(prefix="/api", tags=["targets"])


@router.get("/targets", response_model=list[Target])
async def get_targets(db=Depends(get_db)):
    """Get all targets."""
    cursor = await db.execute("SELECT * FROM targets ORDER BY id")
    rows = await cursor.fetchall()
    return [Target(
        id=row["id"],
        name=row["name"],
        ip=row["ip"],
        interval=row["interval"],
        ping_count=row["ping_count"],
        last_loss=row["last_loss"],
        is_online=bool(row["is_online"])
    ) for row in rows]


@router.post("/targets", response_model=Target, status_code=status.HTTP_201_CREATED)
async def create_target(
    target: TargetCreate,
    db=Depends(get_db),
    current_user = Depends(require_admin)
):
    """Create a new target."""
    import re
    from app.auth import validate_host, clamp_interval
    
    # Validate host format
    if not validate_host(target.ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IP/host format (alphanumeric, dots, and hyphens only)"
        )
    
    # Clamp interval
    interval = clamp_interval(target.interval)
    
    cursor = await db.execute(
        "INSERT INTO targets (name, ip, interval, ping_count, last_loss, is_online) VALUES (?, ?, ?, ?, 0.0, 1)",
        (target.name, target.ip, interval, target.ping_count)
    )
    await db.commit()
    
    new_id = cursor.lastrowid
    return Target(
        id=new_id,
        name=target.name,
        ip=target.ip,
        interval=interval,
        ping_count=target.ping_count,
        last_loss=0.0,
        is_online=True
    )


@router.delete("/targets/{target_id}", response_model=MessageResponse)
async def delete_target(
    target_id: int,
    db=Depends(get_db),
    current_user = Depends(require_admin)
):
    """Delete a target."""
    cursor = await db.execute("SELECT id FROM targets WHERE id = ?", (target_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    await db.execute("DELETE FROM targets WHERE id = ?", (target_id,))
    await db.commit()
    return MessageResponse(message="Target deleted successfully")


@router.put("/targets/{target_id}", response_model=Target)
async def update_target(
    target_id: int,
    target: TargetUpdate,
    db=Depends(get_db),
    current_user = Depends(require_admin)
):
    """Update a target."""
    from app.auth import validate_host, clamp_interval
    
    # Get current target
    cursor = await db.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
    current = await cursor.fetchone()
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    # Validate and apply updates
    name = target.name if target.name is not None else current["name"]
    ip = target.ip if target.ip is not None else current["ip"]
    interval = clamp_interval(target.interval) if target.interval is not None else current["interval"]
    ping_count = target.ping_count if target.ping_count is not None else current["ping_count"]
    
    # Validate new IP if changed
    if target.ip is not None and not validate_host(ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IP/host format"
        )
    
    await db.execute(
        "UPDATE targets SET name = ?, ip = ?, interval = ?, ping_count = ? WHERE id = ?",
        (name, ip, interval, ping_count, target_id)
    )
    await db.commit()
    
    return Target(
        id=target_id,
        name=name,
        ip=ip,
        interval=interval,
        ping_count=ping_count,
        last_loss=current["last_loss"],
        is_online=bool(current["is_online"])
    )


@router.get("/history/{target_name}")
async def get_history(
    target_name: str,
    since: str = None,
    db=Depends(get_db)
):
    """Get history for a target with adaptive compression."""
    from datetime import datetime, timedelta, timezone
    
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            since_dt = datetime.now(timezone.utc) - timedelta(hours=24)
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(hours=24)
    
    cursor = await db.execute(
        "SELECT * FROM history WHERE target_name = ? AND timestamp >= ? ORDER BY timestamp",
        (target_name, since_dt.isoformat())
    )
    rows = await cursor.fetchall()
    
    if not rows:
        return []
    
    # Adaptive compression: raw data for last 24h, hourly aggregate for older
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(hours=24)
    
    if since_dt >= threshold:
        # All data is within 24h - return raw
        return [
            {"timestamp": row["timestamp"], "avg_latency": row["avg_latency"], "loss": row["loss"]}
            for row in rows
        ]
    
    # Mixed: need to split and aggregate older data
    results = []
    hourly_data = {}
    
    for row in rows:
        ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        if ts >= threshold:
            results.append({
                "timestamp": row["timestamp"],
                "avg_latency": row["avg_latency"],
                "loss": row["loss"]
            })
        else:
            # Aggregate by hour
            hour_key = ts.strftime("%Y-%m-%d %H:00:00")
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {"latencies": [], "losses": []}
            hourly_data[hour_key]["latencies"].append(row["avg_latency"])
            hourly_data[hour_key]["losses"].append(row["loss"])
    
    for hour, data in sorted(hourly_data.items()):
        results.append({
            "timestamp": hour,
            "avg_latency": round(sum(data["latencies"]) / len(data["latencies"]), 2),
            "loss": round(sum(data["losses"]) / len(data["losses"]), 2)
        })
    
    return results


@router.get("/sync-status")
async def sync_status(db=Depends(get_db)):
    """Get real-time sync status for dashboard."""
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
