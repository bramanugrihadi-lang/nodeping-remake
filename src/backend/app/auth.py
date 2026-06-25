import re
import asyncio
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from app.schemas import User
import aiosqlite
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: int, role: str) -> str:
    import jwt
    to_encode = {"sub": str(user_id), "role": role}
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db=Depends(get_db)
) -> User:
    import jwt
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload["sub"])
        role = payload["role"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(id=row["id"], username=row["username"], role=row["role"])


async def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


# Rate limiter for login attempts
class LoginRateLimiter:
    def __init__(self):
        self.attempts: Dict[str, Dict] = {}
    
    def _clean_stale(self):
        now = datetime.now()
        self.attempts = {
            ip: data for ip, data in self.attempts.items()
            if data["reset_at"] > now
        }
    
    def _get_or_create_entry(self, ip: str):
        if ip not in self.attempts:
            self.attempts[ip] = {"attempts": 0, "reset_at": None}
        return self.attempts[ip]
    
    async def check(self, ip: str) -> bool:
        """Check if IP is allowed to attempt login. Returns True if allowed."""
        self._clean_stale()
        entry = self._get_or_create_entry(ip)
        
        if entry["attempts"] >= settings.RATE_LIMIT_MAX_ATTEMPTS:
            return False
        
        if entry["attempts"] == 0:
            entry["reset_at"] = datetime.now() + timedelta(minutes=settings.RATE_LIMIT_WINDOW_MINUTES)
        
        entry["attempts"] += 1
        return True
    
    async def reset(self, ip: str):
        """Reset attempts for IP (successful login)."""
        if ip in self.attempts:
            del self.attempts[ip]


def validate_host(host: str) -> bool:
    """Validate host is alphanumeric with dots/hyphens only (no shell metachars)."""
    pattern = r'^[a-zA-Z0-9.\-]+$'
    return bool(re.match(pattern, host))


def clamp_interval(val: int) -> int:
    """Clamp interval to valid range (30-3600 seconds)."""
    return max(30, min(3600, val))


async def ping_target(ip: str, ping_count: int = 4) -> dict:
    """Run ping command and return results."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-c", str(ping_count),
            "-W", "2",
            ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return {
                "avg_latency": 0.0,
                "loss": 100.0,
                "is_online": False
            }
        
        output = stdout.decode()
        
        loss_match = re.search(r'(\d+)%\s*packet\s*loss', output)
        loss = float(loss_match.group(1)) if loss_match else 100.0
        
        lat_match = re.search(r'[\s=](\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*ms', output)
        avg_latency = 0.0
        if lat_match:
            avg_latency = float(lat_match.group(2))
        
        is_online = loss <= 50.0
        
        return {
            "avg_latency": round(avg_latency, 2),
            "loss": round(loss, 2),
            "is_online": is_online
        }
    
    except Exception:
        return {
            "avg_latency": 0.0,
            "loss": 100.0,
            "is_online": False
        }


async def run_ping_cycle(db):
    """Ping all targets sequentially and update history."""
    cursor = await db.execute("SELECT * FROM targets")
    targets = await cursor.fetchall()
    
    for target_row in targets:
        target_name = target_row["name"]
        target_ip = target_row["ip"]
        target_id = target_row["id"]
        ping_count = target_row["ping_count"]
        was_online = bool(target_row["is_online"])
        
        result = await ping_target(target_ip, ping_count)
        
        now = datetime.now(timezone.utc)
        await db.execute(
            "INSERT INTO history (target_name, avg_latency, loss, timestamp) VALUES (?, ?, ?, ?)",
            (target_name, result["avg_latency"], result["loss"], now.isoformat())
        )
        
        await db.execute(
            "UPDATE targets SET last_loss = ?, is_online = ? WHERE id = ?",
            (result["loss"], 1 if result["is_online"] else 0, target_id)
        )
        
        if result["loss"] > 50.0 and was_online:
            print(f"ALERT: {target_name} is DOWN (loss: {result['loss']}%)")
        
        await db.commit()
    
    print(f"[{datetime.now()}] Ping cycle completed for {len(targets)} targets")


# Global rate limiter instance
rate_limiter = LoginRateLimiter()
