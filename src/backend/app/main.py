import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app import routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Initialize database
    await init_db()
    print("✓ Database initialized")
    
    # Start scheduler
    from app.scheduler import start_scheduler
    scheduler_task = asyncio.create_task(start_scheduler())
    
    yield
    
    # Shutdown
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    print("✓ Scheduler stopped")


app = FastAPI(
    title="NodePing API",
    description="Network monitoring API with Telegram alerts and PDF reports",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(routers.auth.router)
app.include_router(routers.targets.router)
app.include_router(routers.sync.router)
app.include_router(routers.users.router)
app.include_router(routers.settings.router)
app.include_router(routers.reports.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
