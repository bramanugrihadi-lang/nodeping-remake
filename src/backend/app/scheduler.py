import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import get_db
from app.auth import run_ping_cycle
from app.pdf_reports import generate_report
from app.config import settings


scheduler = AsyncIOScheduler()


async def run_ping_job():
    """Run ping cycle job."""
    async for db in get_db():
        try:
            await run_ping_cycle(db)
        except Exception as e:
            print(f"Error in ping cycle: {e}")
        finally:
            break


async def run_pdf_job():
    """Generate and send PDF report."""
    async for db in get_db():
        try:
            from app.pdf_reports import generate_and_send_report
            await generate_and_send_report(db)
        except Exception as e:
            print(f"Error generating PDF: {e}")
        finally:
            break


def start_scheduler():
    """Start APScheduler with all jobs."""
    # Ping cycle - run every 60 seconds (minimum interval)
    scheduler.add_job(
        run_ping_job,
        "interval",
        seconds=60,
        id="ping_cycle",
        max_instances=1,
        replace_existing=True
    )
    
    # PDF jobs at 6:00, 12:00, 19:00, 22:00 WIB
    # WIB = UTC+7, so: 23:00, 5:00, 12:00, 15:00 UTC
    scheduler.add_job(
        run_pdf_job,
        "cron",
        hour=23, minute=0,  # 6:00 WIB
        id="pdf_6am",
        max_instances=1,
        replace_existing=True
    )
    scheduler.add_job(
        run_pdf_job,
        "cron",
        hour=5, minute=0,   # 12:00 WIB
        id="pdf_12pm",
        max_instances=1,
        replace_existing=True
    )
    scheduler.add_job(
        run_pdf_job,
        "cron",
        hour=12, minute=0,  # 19:00 WIB
        id="pdf_7pm",
        max_instances=1,
        replace_existing=True
    )
    scheduler.add_job(
        run_pdf_job,
        "cron",
        hour=15, minute=0,  # 22:00 WIB
        id="pdf_10pm",
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Scheduler started with ping cycle and PDF jobs")
    return scheduler


async def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()


if __name__ == "__main__":
    # Test scheduler
    import asyncio
    
    async def test():
        scheduler = start_scheduler()
        await asyncio.sleep(5)
        await stop_scheduler()
        print("✓ Scheduler test completed")
    
    asyncio.run(test())
