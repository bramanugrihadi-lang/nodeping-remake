# NodePing Remake

Network / RTO Monitoring Dashboard — remade from Node.js/Express to modern stack.

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLite + aiosqlite |
| Frontend | React + Vite + Tailwind CSS |
| Scheduler | APScheduler (ping cron, reports) |
| Alerting | Telegram Bot API |
| PDF | ReportLab (server-side) |

## Features

- **Ping monitoring** — TCP ping with configurable interval
- **NOC Dashboard** — Dark theme, KPI cards, latency charts, target status
- **Telegram alerts** — ACK system with auto-recovery notification
- **Scheduled PDF reports** — Daily/weekly report generation
- **Auth** — Admin/Viewer roles, session-based auth
- **History** — Adaptive compression (SmokePing-style retention)

## Setup

### Backend
```bash
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd src/frontend
npm install
npm run dev
```

## Swarm Pipeline

Built using multi-model AI swarm:
- **Orchestrator** — Planning & task decomposition
- **Backend Agent** — Qwen3-Coder-Next
- **Frontend Agent** — Qwen 3.7 Max
- **Reviewer** — DeepSeek V4 Pro

→ [Original NodePing V13](https://github.com/bramanugrihadi-lang/nodeping)