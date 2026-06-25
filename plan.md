# NodePing Remake — Implementation Plan

## Architecture Overview

```
docker-compose
├── backend/          FastAPI + SQLite + APScheduler
│   ├── app/
│   │   ├── main.py           FastAPI app entry
│   │   ├── config.py         Settings from env
│   │   ├── database.py       SQLite init + session
│   │   ├── models.py         SQLAlchemy models
│   │   ├── schemas.py        Pydantic schemas
│   │   ├── auth.py           JWT + password hashing + rate limiter
│   │   ├── ping_engine.py    Subprocess ping + history
│   │   ├── telegram.py       Telegram bot + alerts + ACK polling
│   │   ├── pdf_reports.py    HTML→PDF generation
│   │   ├── scheduler.py      APScheduler cron jobs
│   │   └── routers/
│   │       ├── auth.py       /api/login, /api/me, /api/logout
│   │       ├── targets.py    /api/targets CRUD + /api/history/:name
│   │       ├── users.py      /api/users CRUD (admin)
│   │       ├── settings.py   /api/settings/telegram
│   │       ├── reports.py    /api/reports + /api/generate-pdf-now
│   │       └── sync.py       /api/sync-status
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         React + Vite + Tailwind
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api.js            Axios client + interceptors
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── components/
│   │   │   ├── Layout.jsx          Sidebar + topbar shell
│   │   │   ├── TopBar.jsx          Logo, user, logout
│   │   │   ├── Sidebar.jsx         Target list, search, counts
│   │   │   ├── KPICards.jsx        Total/online/offline/avg latency
│   │   │   ├── TargetDetail.jsx    Latency chart + loss + uptime
│   │   │   ├── TargetForm.jsx      Add/edit modal (admin)
│   │   │   ├── LatencyChart.jsx    Recharts line chart
│   │   │   ├── ProtectedRoute.jsx  Role-based guard
│   │   │   └── Toast.jsx           Notification toast
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       ├── DashboardPage.jsx
│   │       ├── SettingsPage.jsx
│   │       └── ReportsPage.jsx
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## Subtask 1: Project Scaffolding & Database Layer

### Backend
| File | Purpose |
|------|---------|
| `backend/requirements.txt` | fastapi, uvicorn, sqlalchemy, aiosqlite, pyjwt, passlib[bcrypt], python-multipart, apscheduler, httpx, weasyprint, jinja2, pydantic-settings |
| `backend/app/config.py` | `class Settings(BaseSettings): SECRET_KEY, ADMIN_PASSWORD, DATABASE_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, JWT_EXPIRY_HOURS=12` |
| `backend/app/database.py` | `get_db()` async generator, `init_db()` creates tables + seeds default admin |
| `backend/app/models.py` | SQLAlchemy models (see schema below) |
| `backend/app/schemas.py` | Pydantic request/response schemas for all entities |

**SQLAlchemy Models:**
```python
class User(Base):
    id: int (PK)
    username: str (unique)
    password_hash: str
    role: str  # "admin" | "viewer"

class Target(Base):
    id: int (PK)
    name: str (unique)
    ip: str
    interval: int  # seconds, 30-3600
    ping_count: int  # packets per ping cycle
    last_loss: float  # 0-100
    is_online: bool

class History(Base):
    id: int (PK)
    target_name: str (FK)
    avg_latency: float  # ms
    loss: float  # 0-100
    timestamp: datetime  # UTC

class Setting(Base):
    key: str (PK)
    value: str  # JSON-encoded

class PDFReport(Base):
    id: int (PK)
    filename: str
    generated_at: datetime
    file_path: str
```

**Seed default admin:** `admin` / `admin123` with bcrypt hash, inserted if users table is empty.

### Frontend
| File | Purpose |
|------|---------|
| `frontend/` | Vite scaffold: `npm create vite@latest frontend -- --template react` |
| `frontend/tailwind.config.js` | Dark theme palette: bg #0a0e17, surface #111827, accent #3b82f6, green #22c55e, red #ef4444 |
| `frontend/src/api.js` | Axios instance with baseURL `/api`, request interceptor attaches JWT `Authorization: Bearer`, response interceptor redirects to `/login` on 401 |
| `frontend/src/context/AuthContext.jsx` | `AuthProvider` with `{user, token, login, logout, isAdmin}` |

**Success Criteria:**
- `docker-compose up` starts both services
- Backend returns 200 on `GET /api/me` with valid token
- Frontend login page renders at `http://localhost:3000`
- Default admin can log in

---

## Subtask 2: Auth System (JWT + Rate Limiter + Roles)

### Backend
| File | Function | Behavior |
|------|----------|----------|
| `backend/app/auth.py` | `hash_password(pw: str) -> str` | bcrypt via passlib |
| `backend/app/auth.py` | `verify_password(pw: str, hash: str) -> bool` | bcrypt verify |
| `backend/app/auth.py` | `create_token(user_id: int, role: str) -> str` | JWT with `sub`, `role`, `exp` (12h) |
| `backend/app/auth.py` | `get_current_user(token, db) -> User` | FastAPI dependency, decodes JWT, fetches user |
| `backend/app/auth.py` | `require_admin(current_user) -> User` | Raises 403 if role != "admin" |
| `backend/app/auth.py` | `LoginRateLimiter` class | In-memory dict: `{ip: {attempts, reset_at}}`. 5 attempts, 15min window. Auto-cleanup stale entries. |
| `backend/app/routers/auth.py` | `POST /api/login` | Body: `{username, password}`. Rate-limited. Returns `{token, user: {id, username, role}}` |
| `backend/app/routers/auth.py` | `GET /api/me` | Returns current user info from token |
| `backend/app/routers/auth.py` | `POST /api/logout` | Stateless JWT — client discards token. Server returns 200 OK. |

### Frontend
| File | Component | Behavior |
|------|-----------|----------|
| `frontend/src/pages/LoginPage.jsx` | `LoginPage` | Dark centered card. Username + password fields. Error message on failure. Redirects to `/` on success. Shows "Too many attempts" after 5 failures. |
| `frontend/src/components/ProtectedRoute.jsx` | `ProtectedRoute` | Wraps children. If no token → redirect `/login`. If `requireAdmin` prop and user is viewer → redirect `/` with toast. |

**Success Criteria:**
- `POST /api/login` with admin/admin123 returns JWT
- `GET /api/me` returns user info
- 6th login attempt within 15min returns 429
- Non-admin hitting admin-only endpoint returns 403
- Token expires after 12h — 401 response

---

## Subtask 3: Ping Monitoring Engine + History

### Backend
| File | Function | Behavior |
|------|----------|----------|
| `backend/app/ping_engine.py` | `async def ping_target(target: Target) -> dict` | Runs `ping -c {count} -W 2 {ip}` via `asyncio.create_subprocess_exec` (list args, no shell). Parses stdout for avg latency and loss %. Returns `{avg_latency, loss, is_online}`. |
| `backend/app/ping_engine.py` | `async def run_ping_cycle(db)` | Iterates all targets sequentially. For each: calls `ping_target()`, inserts History row, updates `target.last_loss` and `target.is_online`. If loss > 50% and target was previously online → trigger alert. |
| `backend/app/ping_engine.py` | `validate_host(host: str) -> bool` | Regex: `^[a-zA-Z0-9.-]+$` (no spaces, no shell metachars). |
| `backend/app/ping_engine.py` | `clamp_interval(val: int) -> int` | `max(30, min(3600, val))` |
| `backend/app/history.py` | `async def get_history(target_name, since, db) -> list` | Adaptive compression: if `since < 24h` → return raw rows. If older → return hourly aggregates (AVG latency, AVG loss). |
| `backend/app/scheduler.py` | `start_scheduler()` | APScheduler: scans all targets, finds min interval. Runs `run_ping_cycle` at that interval. Reschedules on target CRUD changes. |

### Frontend
| File | Component | Behavior |
|------|-----------|----------|
| `frontend/src/pages/DashboardPage.jsx` | `DashboardPage` | Layout shell: TopBar + Sidebar + main content area. Polls `GET /api/sync-status` every 5s for real-time data. |
| `frontend/src/components/TopBar.jsx` | `TopBar` | Logo "NodePing", username badge, logout button. |
| `frontend/src/components/Sidebar.jsx` | `Sidebar` | Target list with green/red dot indicators. Search filter input. Summary counts (total/online/offline). Click to select target. |
| `frontend/src/components/KPICards.jsx` | `KPICards` | 4 cards: Total Targets, Online, Offline, Avg Latency. Animated counters. |
| `frontend/src/components/TargetDetail.jsx` | `TargetDetail` | Selected target detail: LatencyChart (24h), packet loss list, uptime %, edit/delete buttons (admin only). |
| `frontend/src/components/LatencyChart.jsx` | `LatencyChart` | Recharts `<LineChart>` with latency over time. Dark theme colors. |
| `frontend/src/components/TargetForm.jsx` | `TargetForm` | Modal form: name, IP/host, interval slider (30-3600), ping count. Used for both add and edit. Validates host regex client-side. |

**Success Criteria:**
- Adding a target starts pinging it within one cycle
- History rows appear in DB with correct latency/loss
- `GET /api/history/:name` returns raw data for last 24h, aggregated for older
- Downtime event fires alert when loss > 50%
- Dashboard shows real-time status (polling)

---

## Subtask 4: Telegram Alerts + ACK System

### Backend
| File | Function | Behavior |
|------|----------|----------|
| `backend/app/telegram.py` | `TelegramNotifier` class | Init with token + chat_id from settings table. `async def send_alert(target_name, loss, latency)` — formats message with target name, loss%, latency, timestamp. Includes inline keyboard `[Acknowledge]`. |
| `backend/app/telegram.py` | `async def send_pdf(chat_id, file_path)` | Sends PDF document via Telegram Bot API. |
| `backend/app/telegram.py` | `async def poll_updates()` | Background task: polls `getUpdates` every 10s. Checks for callback queries with ACK. Updates `alert_acknowledged` flag in DB. |
| `backend/app/routers/settings.py` | `GET /api/settings/telegram` | Returns `{token, chat_id}` (token masked: show last 4 chars). Admin only. |
| `backend/app/routers/settings.py` | `POST /api/settings/telegram` | Body: `{token, chat_id}`. Upserts settings table. Admin only. |

### Frontend
| File | Component | Behavior |
|------|-----------|----------|
| `frontend/src/pages/SettingsPage.jsx` | `SettingsPage` | Tabbed: Telegram config, PDF schedule, User management. Admin only. |
| `frontend/src/components/TelegramConfig.jsx` | (embedded in SettingsPage) | Token input (password field), Chat ID input. Save button. Shows masked token when loaded. |

**Success Criteria:**
- When target goes down (loss > 50%), Telegram message is sent
- Message contains target name, loss%, latency, timestamp
- Message has "Acknowledge" button
- Clicking ACK in Telegram updates state server-side
- Settings page saves/loads Telegram config

---

## Subtask 5: PDF Reports + User Management

### Backend
| File | Function | Behavior |
|------|----------|----------|
| `backend/app/pdf_reports.py` | `async def generate_report(db) -> str` | Queries all targets with their 24h history. Renders Jinja2 HTML template. Converts to PDF via weasyprint. Saves to `reports/` directory. Inserts `PDFReport` row. Returns file path. |
| `backend/app/pdf_reports.py` | `report_template.html` | Jinja2 template: dark NOC theme, table of targets with uptime %, latency chart images (base64-encoded matplotlib), timestamp, header. |
| `backend/app/scheduler.py` | `schedule_pdf_jobs()` | APScheduler cron jobs at 6:00, 12:00, 19:00, 22:00 WIB (UTC+7 → 23:00, 5:00, 12:00, 15:00 UTC). Each generates report + sends via Telegram. |
| `backend/app/routers/reports.py` | `GET /api/reports` | Returns list of PDFReport rows (id, filename, generated_at). Admin only. |
| `backend/app/routers/reports.py` | `POST /api/generate-pdf-now` | Triggers immediate report generation. Admin only. |
| `backend/app/routers/reports.py` | `GET /api/reports/{id}/download` | Returns PDF file as `application/pdf` download. |
| `backend/app/routers/users.py` | `GET /api/users` | List all users (exclude password_hash). Admin only. |
| `backend/app/routers/users.py` | `POST /api/users` | Body: `{username, password, role}`. Creates user. Admin only. |
| `backend/app/routers/users.py` | `DELETE /api/users/{id}` | Delete user. Cannot delete self. Admin only. |

### Frontend
| File | Component | Behavior |
|------|-----------|----------|
| `frontend/src/pages/ReportsPage.jsx` | `ReportsPage` | Table of past reports with date/time. Download button per row. "Generate Now" button at top (admin only). |
| `frontend/src/components/UserManagement.jsx` | (embedded in SettingsPage) | Table of users. Add user form (username, password, role dropdown). Delete button per row (cannot delete self). |

**Success Criteria:**
- PDF generates with all targets, uptime stats, latency charts
- Scheduled PDFs fire at correct times (6am, 12pm, 7pm, 10pm)
- Manual generate button works and returns PDF
- User CRUD works: admin can add/delete users
- Cannot delete own user account

---

## Backend API Design (Complete)

| Method | Path | Auth | Role | Request Body | Response |
|--------|------|------|------|-------------|----------|
| POST | `/api/login` | No | — | `{username, password}` | `{token, user}` |
| GET | `/api/me` | Yes | Any | — | `{id, username, role}` |
| POST | `/api/logout` | Yes | Any | — | `{message}` |
| GET | `/api/targets` | Yes | Any | — | `[{id, name, ip, interval, ping_count, last_loss, is_online}]` |
| POST | `/api/targets` | Yes | Admin | `{name, ip, interval, ping_count}` | `{id, ...}` |
| DELETE | `/api/targets/{id}` | Yes | Admin | — | `{message}` |
| PUT | `/api/targets/{id}` | Yes | Admin | `{name, ip, interval, ping_count}` | `{id, ...}` |
| GET | `/api/history/{name}` | Yes | Any | `?since=ISO8601` | `[{timestamp, avg_latency, loss}]` |
| GET | `/api/users` | Yes | Admin | — | `[{id, username, role}]` |
| POST | `/api/users` | Yes | Admin | `{username, password, role}` | `{id, ...}` |
| DELETE | `/api/users/{id}` | Yes | Admin | — | `{message}` |
| GET | `/api/settings/telegram` | Yes | Admin | — | `{token (masked), chat_id}` |
| POST | `/api/settings/telegram` | Yes | Admin | `{token, chat_id}` | `{message}` |
| GET | `/api/reports` | Yes | Admin | — | `[{id, filename, generated_at}]` |
| POST | `/api/generate-pdf-now` | Yes | Admin | — | `{id, filename}` |
| GET | `/api/reports/{id}/download` | Yes | Any | — | `application/pdf` |
| GET | `/api/sync-status` | Yes | Any | — | `{targets: [...], summary: {total, online, offline, avg_latency}}` |

---

## Frontend Component Tree

```
<App>
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />}>
              <!-- <TopBar /> -->
              <!-- <Sidebar /> -->
              <!-- <KPICards /> -->
              <!-- <TargetDetail> -->
              <!--   <LatencyChart /> -->
              <!--   <TargetForm /> (modal) -->
              <!-- </TargetDetail> -->
            </Route>
            <Route path="/settings" element={<ProtectedRoute requireAdmin />}>
              <Route index element={<SettingsPage />}>
                <!-- Telegram config -->
                <!-- PDF schedule -->
                <!-- <UserManagement /> -->
              </Route>
            </Route>
            <Route path="/reports" element={<ReportsPage />}>
              <!-- Report list table -->
              <!-- Generate button -->
              <!-- Download links -->
            </Route>
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  </AuthProvider>
</App>
```

---

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - SECRET_KEY=...
      - ADMIN_PASSWORD=admin123
      - DATABASE_URL=sqlite+aiosqlite:///./data/nodeping.db
    volumes:
      - ./data:/app/data
      - ./reports:/app/reports

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
```

Nginx in frontend container proxies `/api/*` to `backend:8000`.

---

## Success Criteria (Overall)

1. **Auth:** Login with admin/admin123 works. Rate limiter blocks at 6th attempt. Viewer cannot access admin endpoints. JWT expires after 12h.
2. **Ping:** Adding a target starts pinging. History stores correctly. Adaptive compression returns raw data for <24h, aggregated for older.
3. **Alerts:** Target DOWN triggers Telegram message with ACK button. ACK is registered server-side.
4. **PDF:** Scheduled reports generate at 4 configured times. Manual generate works. PDFs downloadable from reports page.
5. **UI:** Dark NOC theme renders correctly. Real-time dashboard updates via polling. All CRUD operations work from UI.
6. **Security:** No shell injection via host field. All endpoints except `/api/login` require auth. Admin-only endpoints enforce role check.
7. **Deploy:** Single `docker-compose up` brings everything online. Frontend accessible at port 3000.