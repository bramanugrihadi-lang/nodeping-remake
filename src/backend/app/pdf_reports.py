import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML
import aiofiles
from app.database import get_db
from app.telegram import TelegramNotifier
from app.config import settings


REPORTS_DIR = Path(__file__).parent.parent / "reports"


async def generate_report(db) -> str:
    """Generate PDF report for all targets."""
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Get all targets
    cursor = await db.execute("SELECT * FROM targets ORDER BY id")
    targets = await cursor.fetchall()
    
    # Get 24h history for each target
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    
    target_data = []
    for t in targets:
        cursor = await db.execute(
            """SELECT timestamp, avg_latency, loss 
               FROM history 
               WHERE target_name = ? AND timestamp >= ?
               ORDER BY timestamp""",
            (t["name"], since.isoformat())
        )
        history = await cursor.fetchall()
        
        # Calculate stats
        if history:
            losses = [h["loss"] for h in history]
            latencies = [h["avg_latency"] for h in history]
            avg_loss = sum(losses) / len(losses)
            avg_latency = sum(latencies) / len(latencies)
            uptime = (sum(1 for h in history if h["loss"] <= 50) / len(history)) * 100
        else:
            avg_loss = 0.0
            avg_latency = 0.0
            uptime = 100.0
        
        target_data.append({
            "name": t["name"],
            "ip": t["ip"],
            "is_online": bool(t["is_online"]),
            "avg_loss": avg_loss,
            "avg_latency": avg_latency,
            "uptime": uptime,
            "history": history
        })
    
    # Render template
    try:
        env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
        template = env.get_template("report_template.html")
    except TemplateNotFound:
        # Fallback inline template
        template_content = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NodePing Report - {{ generated_at }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0a0e17; color: #fff; padding: 20px; }
        h1 { text-align: center; color: #3b82f6; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .card { background: #111827; padding: 15px; border-radius: 8px; text-align: center; flex: 1; }
        .card h3 { margin: 0; font-size: 0.9em; color: #9ca3af; }
        .card .value { font-size: 1.5em; font-weight: bold; color: #fff; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #374151; }
        th { background: #1f2937; }
        .online { color: #22c55e; }
        .offline { color: #ef4444; }
    </style>
</head>
<body>
    <h1>NodePing Network Report</h1>
    <p>Generated: {{ generated_at }}</p>
    
    <div class="summary">
        <div class="card"><h3>Total Targets</h3><div class="value">{{ total_targets }}</div></div>
        <div class="card"><h3>Online</h3><div class="value">{{ online }}</div></div>
        <div class="card"><h3>Offline</h3><div class="value">{{ offline }}</div></div>
        <div class="card"><h3>Avg Loss</h3><div class="value">{{ avg_loss }}%</div></div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>IP</th>
                <th>Status</th>
                <th>Uptime</th>
                <th>Avg Loss</th>
                <th>Avg Latency</th>
            </tr>
        </thead>
        <tbody>
            {% for t in targets %}
            <tr>
                <td>{{ t.name }}</td>
                <td>{{ t.ip }}</td>
                <td class="{{ 'online' if t.is_online else 'offline' }}">
                    {{ 'ONLINE' if t.is_online else 'OFFLINE' }}
                </td>
                <td>{{ t.uptime|round(1) }}%</td>
                <td>{{ t.avg_loss|round(1) }}%</td>
                <td>{{ t.avg_latency|round(1) }}ms</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""
        env = Environment()
        template = env.from_string(template_content)
    
    # Render HTML
    html_content = template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        total_targets=len(target_data),
        online=sum(1 for t in target_data if t["is_online"]),
        offline=sum(1 for t in target_data if not t["is_online"]),
        avg_loss=sum(t["avg_loss"] for t in target_data) / len(target_data) if target_data else 0,
        targets=target_data
    )
    
    # Generate PDF
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.pdf"
    file_path = REPORTS_DIR / filename
    
    HTML(string=html_content, base_url=str(Path(__file__).parent)).write_pdf(str(file_path))
    
    # Save to DB
    from app.models import PDFReport
    await db.execute(
        "INSERT INTO pdf_reports (filename, generated_at, file_path) VALUES (?, ?, ?)",
        (filename, datetime.now(timezone.utc).isoformat(), str(file_path))
    )
    await db.commit()
    
    return str(file_path)


async def generate_and_send_report(db):
    """Generate report and send via Telegram if configured."""
    file_path = await generate_report(db)
    
    if settings.TELEGRAM_TOKEN and settings.TELEGRAM_CHAT_ID:
        notifier = TelegramNotifier()
        await notifier.send_pdf(settings.TELEGRAM_CHAT_ID, file_path)
        print(f"✓ PDF report sent: {file_path}")
    else:
        print(f"✓ PDF report generated: {file_path}")


if __name__ == "__main__":
    async def test():
        async for db in get_db():
            file_path = await generate_report(db)
            print(f"Generated: {file_path}")
            break
    
    asyncio.run(test())
