import asyncio
import aiosqlite
from pathlib import Path
from app.config import settings

DB_PATH = Path(__file__).parent.parent / "data" / "nodeping.db"


async def get_db():
    """Async database session generator."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    """Initialize database with tables and seed default admin if empty."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer'
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                ip TEXT NOT NULL,
                interval INTEGER NOT NULL DEFAULT 60,
                ping_count INTEGER NOT NULL DEFAULT 4,
                last_loss REAL NOT NULL DEFAULT 0.0,
                is_online INTEGER NOT NULL DEFAULT 1
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_name TEXT NOT NULL,
                avg_latency REAL NOT NULL DEFAULT 0.0,
                loss REAL NOT NULL DEFAULT 0.0,
                timestamp TEXT NOT NULL
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        """)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                loss REAL NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # Seed default admin if users table is empty
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]
        
        if count == 0:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_hash = pwd_context.hash(settings.ADMIN_PASSWORD)
            
            await cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", password_hash, "admin")
            )
            print("✓ Default admin user created (admin/admin123)")
        
        await db.commit()
