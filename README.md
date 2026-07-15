# Foodly

**AI-powered, community-verified food discovery platform for Islamabad & Rawalpindi.**

Foodly helps users find nearby, affordable meals with live price updates, semantic search, GPS filtering, and AI-generated value insights. Built as a production-grade startup MVP targeting a PKR 15M seed round.

> **Note on this revision:** This README replaces a version whose "Known Issues" and tech-stack sections had drifted from the actual code (e.g. it still described admin auth as a shared-secret header and CORS as wildcard, both of which were fixed). This version was corrected against a line-level audit of the current codebase. See [Known Issues](#known-issues) for what's actually still open.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [AI Architecture](#ai-architecture)
5. [Security Architecture](#security-architecture)
6. [Caching Architecture (Redis)](#caching-architecture-redis)
7. [Real-time Architecture (WebSockets)](#real-time-architecture-websockets)
8. [Event-driven Architecture (Kafka)](#event-driven-architecture-kafka)
9. [Infrastructure & DevOps](#infrastructure--devops)
10. [Database Schema](#database-schema)
11. [API Reference](#api-reference)
12. [Project Structure](#project-structure)
13. [Local Setup](#local-setup)
14. [Environment Variables](#environment-variables)
15. [Foodly Score Algorithm](#foodly-score-algorithm)
16. [Known Issues](#known-issues)
17. [Execution Plan](#execution-plan)

---

## What It Does

| Feature | Description | Status |
|---------|-------------|--------|
| **Geo-filtered search** | Meals within a configurable radius, sorted by PostGIS distance | ✅ Live |
| **Semantic search** | pgvector cosine similarity — understands "student budget lunch" without exact keywords | ✅ Live |
| **Live web intelligence** | LangGraph agent searches the web in real time, streams results via SSE | ✅ Live |
| **AI value insights** | LangChain + Gemini generates grounded verdict using real market price data (RAG) | ✅ Live |
| **Confidence score system** | Every meal starts at 100%, decays 5pts per pending report, restores on admin approval | ✅ Live |
| **Community price reports** | Users submit price updates with optional photo; admin moderates; free-text fields sanitized (`bleach`) | ✅ Live |
| **Human-in-the-loop (HITL)** | Web agent findings pause for admin review via LangGraph `interrupt()` before applying to DB | ✅ Live |
| **Conversational assistant** | ReAct agent with 5 DB-backed tools, streamed over SSE — "find something under PKR 200 near NUST, not biryani" | ✅ Live |
| **Role-based admin auth** | JWT `role` claim + DB-backed `require_admin` check, no shared secret | ✅ Live |
| **Rate limiting** | Per-user (JWT) or per-IP, tiered by endpoint cost (`slowapi`) | ✅ Live |
| **Security headers + structured logging** | OWASP headers on every response; `structlog` JSON logs on hot paths | ✅ Live |
| **Personalized feed** | User taste embedding centroid blended into ranking | ⬜ Planned |
| **Nightly enrichment supervisor** | Multi-agent fan-out via LangGraph `Send()` | ⬜ Planned |
| **Saved meals** | Authenticated bookmarks synced to DB | ✅ Live |
| **Admin dashboard** | Real-time stats, report queue, moderation | ✅ Live |

---

## Tech Stack

### Backend (Current — verified against `requirements.txt` and source)
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | 0.136 |
| Language | Python | 3.11 |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL + PostGIS + pgvector | 15 |
| Auth | python-jose (JWT HS256) + passlib bcrypt | — |
| Rate limiting | slowapi (user-ID-aware, IP fallback) | — |
| Security headers | Custom middleware (OWASP headers) | — |
| Structured logging | structlog (hot paths: auth, reports, admin) | — |
| Input sanitization | bleach (report `notes`/`reporter_name`) | — |
| AI Orchestration | LangGraph | 1.1 |
| AI Chains | LangChain LCEL | 1.2 |
| LLM — Reasoning/Insight | Google Gemini 2.0 Flash | — |
| LLM — Structured Output/Chat | Groq llama-3.3-70b-versatile | — |
| Embeddings | Google Gemini text-embedding-004 | 1536-dim |
| Web Search | Tavily Search API | — |
| Real-time (current) | SSE via sse-starlette | — |
| Cache | Redis (insight caching live; broader hot-path caching planned) | — |
| Automation | N8N webhooks | — |
| Server | Uvicorn | — |

### Backend (Planned)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Broader Redis caching | Redis | Sub-150ms `/search`, `/nearby`, `/feed` responses |
| Message broker | Apache Kafka | Decouple HTTP handlers from side effects |
| WebSockets | FastAPI native | Live notifications, search suggestions, agent events |
| AI observability | LangSmith | Trace every LangGraph/LangChain call, token cost tracking |
| Async workers | Python asyncio consumers | Notification, cache invalidation, email, scraper workers |
| Containerization | Docker + Docker Compose | Full-stack one-command startup (currently only `redis` service defined) |
| CI/CD | GitHub Actions | Automated test → build → deploy pipeline |
| Cloud | AWS ECS Fargate + RDS + ElastiCache | Production deployment |
| Monitoring | CloudWatch + Sentry + Prometheus | Alerting, dashboards, error tracking |

### Frontend (Current)
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js | 16 |
| Runtime | React | 19 |
| Language | TypeScript | 5 |
| Styling | Tailwind CSS | 4 |
| Animation | Framer Motion | 12 |
| Maps | React Leaflet + OpenStreetMap | 5 |
| Icons | Lucide React | — |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  Next.js 16 · React Leaflet · Framer Motion · TypeScript            │
│  REST (fetch) · SSE (EventSource, chat + live-price)                │
└────────────────────────────┬────────────────────────────────────────┘
                              │ HTTPS
┌────────────────────────────▼────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│                    FastAPI · Uvicorn                                │
│                                                                      │
│  ┌──────────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │  REST API    │  │  SSE     │  │  SSE        │  │  Rate limit  │  │
│  │  /api/v1/*   │  │  /chat   │  │  /agent/    │  │  + security  │  │
│  │              │  │          │  │  live-price │  │  headers     │  │
│  └──────┬───────┘  └────┬─────┘  └──────┬──────┘  └──────────────┘  │
│         │               │               │                          │
│  ┌──────▼───────────────▼───────────────▼───────────────────────┐  │
│  │                     SERVICE LAYER                            │  │
│  │  MealService · AuthService (JWT+role) · ReportService         │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
│                             │                                      │
│  ┌──────────────────────────▼──────────────────────────────────┐  │
│  │                   AI WORKFLOW LAYER                          │  │
│  │                                                               │  │
│  │  LangGraph Graphs              LangChain Chains               │  │
│  │  ├─ price_agent (HITL)         ├─ insight_chain (RAG)         │  │
│  │  └─ assistant_graph (ReAct)    ├─ query_expansion_chain       │  │
│  │                                 ├─ report_validation_chain    │  │
│  │                                 └─ refine_query_chain         │  │
│  │                                                               │  │
│  │  Tools: Tavily · pgvector · DB queries (foodly_tools.py)      │  │
│  └──────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                        DATA LAYER                                  │
│  PostgreSQL 15 (PostGIS + pgvector + LangGraph checkpointer)        │
│  Redis (insight cache; broader hot-path caching planned)             │
└──────────────────────────────────────────────────────────────────────┘
```

Kafka, WebSockets, and full multi-service Docker Compose are **planned, not yet implemented** — see [Execution Plan](#execution-plan).

---

## AI Architecture

### AI Feature Map

| Feature | Tool | Graph / Chain | Status |
|---------|------|--------------|--------|
| Semantic search embeddings | Gemini `text-embedding-004` + pgvector | — | ✅ Live |
| Live price scraper (HITL) | LangGraph `StateGraph` + Groq + Tavily | `price_agent` | ✅ Live |
| Grounded RAG insight | LangChain LCEL + pgvector context + Gemini | `insight_chain` | ✅ Live (see [Known Issues](#known-issues) — thread safety) |
| Smart query expansion | LangChain LCEL + Groq | `query_expansion_chain` | ✅ Live |
| AI report validator | LangChain LCEL + Groq, structured output | `report_validation_chain` | ✅ Live |
| Query refinement (low-confidence retry) | LangChain LCEL + Groq | `refine_query_chain` | ✅ Live |
| Conversational assistant | LangGraph ReAct + 5 DB tools | `assistant_graph` | ✅ Live |
| Personalized feed | LangChain LCEL + pgvector centroid | `personalization_chain` | ⬜ Planned |
| Nightly enrichment supervisor | LangGraph multi-agent `Send()` | `supervisor_graph` | ⬜ Planned |
| AI observability | LangSmith tracing + eval datasets | — | ⬜ Planned |
| Unified fallback wrapper | `safe_invoke` | all chains | ⬜ Planned (ad-hoc try/except per call site today) |

---

### 1. LangGraph Price Scraper (`price_agent`)
**File:** `backend/ai/agents/price_scraper.py`

```
[search_node] → [extract_node] → should_continue()
                                      ├─ "store"        → [store_node] → END   (confidence ≥ 50)
                                      ├─ "retry"         → [retry_node] → search (confidence < 50, iter < 3)
                                      └─ "end"/"paused"  → [human_review_node] (interrupt) → resume via admin
```

**State:** `AgentState(search_query, search_results, extracted_data, iterations, meal_id, thread_id, validation_passed, retry_reason)`

**LLMs used:**
- `search_node` — Tavily Search API (web retrieval, async wrapper over sync client)
- `extract_node` — Groq `llama-3.3-70b` with `with_structured_output(ExtractedPrice)`
- `retry_node` — Groq generates a refined search query when confidence < 50

**HITL:** Compiled with `interrupt_before=["human_review"]` and an `AsyncPostgresSaver` checkpointer — state survives server restarts. Admin resumes via `POST /api/v1/agent/resume/{thread_id}`.

**Streamed via SSE** to frontend as `starting → searching → extracting → paused/complete/failed` events.

---

### 2. LangGraph Conversational Assistant (`assistant_graph`)
**File:** `backend/ai/graph/assistant_graph.py`

A ReAct agent (`create_react_agent`) with 5 domain-specific tools (`backend/ai/tools/foodly_tools.py`), each opening its own short-lived `SessionLocal()` per call rather than sharing a session across concurrent tool invocations:

```python
@tool async def search_nearby_meals(lat, lng, radius_km, max_price) → list[dict]
@tool async def filter_meals(meals, exclude_category, min_confidence) → list[dict]
@tool async def get_meal_insight(meal_id) → str
@tool async def get_price_trend(meal_id) → str   # rising | falling | stable
@tool async def semantic_search_meals(query, limit) → list[dict]
```

System prompt scopes the agent to Islamabad/Rawalpindi food discovery only; off-topic requests are declined. Multi-turn context persists via `AsyncPostgresSaver` checkpointer, keyed by `thread_id`. Streamed via SSE at `POST /api/v1/chat`: `thinking → tool_call → tool_result → token → done`.

---

### 3. LangChain RAG Insight Chain (`insight_chain`)
**File:** `backend/ai/chains/insight_chain.py`

```python
chain = (
    RunnableParallel({
        "similar_meals":  ...,   # pgvector top-5 by cosine similarity
        "sector_stats":   ...,   # avg/min/max price filtered by location
        "price_history":  ...,   # last 10 approved reports
        "meal":           ...,
    })
    | INSIGHT_PROMPT
    | ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    | JsonOutputParser()
    | _validate_insight_output
)
```

Context retrieval for the three parallel branches currently runs inside a `ThreadPoolExecutor` **sharing one SQLAlchemy `Session`** across threads — this is a known thread-safety issue (SQLAlchemy sessions are not thread-safe). See [Known Issues](#known-issues). Falls back to the legacy single-shot `agents.py:generate_value_insight` if RAG generation fails, and further to a keyword-templated response if that fails too — no unhandled 500s from this path.

---

## Security Architecture

### Authentication & Authorization

**JWT (HS256)**
- Payload: `{ sub: user.email, role: user.role, exp: now + ACCESS_TOKEN_EXPIRE_MINUTES }`
- `SECRET_KEY` required at startup, minimum 32 bytes, rejected if it matches a known placeholder value (`config.py` fails fast — see below)
- Every protected route validates the token and loads the user via `Depends(get_current_user)`

**Admin access — role-based JWT, not a shared secret**
- `role` column on `User` (`'user' | 'admin'`), defaulted `'user'`, **never settable via the public register endpoint**
- `require_admin` dependency re-checks the **live DB role** on every request (not just the JWT claim), so revocation is immediate — a demoted admin loses access on their very next request, without waiting for token expiry
- Promotion is manual only, via `backend/scripts/promote_admin.py` — never exposed as an API endpoint, since a self/other-promotion endpoint is itself a privilege-escalation surface

**Password hashing**
- bcrypt via `passlib`, cost factor default (12)
- Register returns the user object only — never the password hash

**Fail-fast secrets (`backend/app/core/config.py`)**
- `SECRET_KEY` and `DATABASE_URL` are **required**, with no default fallback — the app refuses to start rather than boot against an insecure guessable default
- `SECRET_KEY` is additionally checked against a placeholder blocklist (`"change-me"`, `"secret"`, `"password"`, etc.) and a minimum-length requirement (32 bytes)

---

### OWASP Top 10 Hardening — Actual Status

| Threat | Mitigation | Status |
|--------|-----------|--------|
| **A01 Broken Access Control** | Role-based JWT + live DB re-check on every admin request | ✅ Live |
| **A02 Cryptographic Failures** | bcrypt hashing, JWT HS256, fail-fast on weak/missing `SECRET_KEY` | ✅ Live |
| **A03 SQL Injection** | SQLAlchemy ORM only, zero raw string interpolation | ✅ Live by construction |
| **A04 Insecure Design** | Route → Service → Repository layering enforced | ✅ Live |
| **A05 Security Misconfiguration** | Env-driven CORS whitelist (`ALLOWED_ORIGINS`), no wildcard | ✅ Live |
| **A07 Auth Failures** | `/auth/login` rate-limited 5/min per key; same 401 for wrong email vs. password | ✅ Live |
| **A09 Logging Failures** | `structlog` JSON logs on auth/reports/admin hot paths | 🔶 Partial — full `print()` removal across the backend still pending |

**Security headers middleware** (`backend/app/core/security_headers.py`, applied to every response):
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

**XSS prevention:** `bleach.clean(tags=[], strip=True)` applied to `notes` and `reporter_name` in `reports.py` before DB write, since these render unescaped in the admin dashboard.

---

### Rate Limiting — Actual Config (`backend/app/core/rate_limit.py`, `slowapi`)

Key strategy: **JWT `sub` claim when present, IP fallback for anonymous requests** — more accurate than pure IP limiting (shared WiFi undercounts distinct users; IP-only limiting is trivially evaded by switching networks while logged in).

| Endpoint | Limit | Scope |
|----------|-------|-------|
| `POST /auth/login` | 5/min | user-or-IP key |
| `GET /meals` (list/search) | 30/min | user-or-IP key |
| `POST /reports` | 10/min | user-or-IP key |
| `GET /agent/live-price` | 5/min | user-or-IP key |
| `POST /chat` | 10/min | user-or-IP key (same tier as live-price — both are AI-cost-sensitive) |
| Global default (no explicit decorator) | 100/min | user-or-IP key |

All violations return `429` via slowapi's default handler.

---

## Caching Architecture (Redis)

**Status: partial.** `backend/app/core/cache.py` (`get_cached`/`set_cached`, async, JSON-serialized, TTL-based) is implemented and used today for:
- AI insight caching (`insight:{meal_id}:{price}` — key includes price so it auto-invalidates on price change, 24h TTL)
- Semantic search result caching (`search_cache:{hash}`, 1h TTL)

**Not yet implemented:** `/nearby` caching, `/feed` caching, semantic cache for `/chat`, `X-Cache` response header, cache invalidation on writes beyond price-keyed insight caching, Redis health check in `/health`. See [Execution Plan](#execution-plan) Sprint 11–12.

---

## Real-time Architecture (WebSockets)

**Status: not yet implemented.** Current real-time delivery is SSE only (`/chat`, `/agent/live-price`). WebSocket connection manager, live notifications (report approved/rejected, price changes to saved meals), and agent-event multiplexing are planned — see [Execution Plan](#execution-plan) Sprints 14–17.

---

## Event-driven Architecture (Kafka)

**Status: not yet implemented.** All side effects (WS push, cache invalidation, email, n8n webhook) currently run inline in HTTP handlers or as FastAPI `BackgroundTasks` (see `reports.py`'s `_notify_n8n`). Kafka topics, workers, and DLQ are planned — see [Execution Plan](#execution-plan) Sprints 18–22.

---

## Infrastructure & DevOps

**Current `docker-compose.yml`** defines exactly one service: `redis`. Postgres, the backend, the frontend, and all planned workers are not yet containerized — local setup currently runs each piece manually (`venv` + `uvicorn`, `npm run dev`). Full multi-service Compose, CI/CD (GitHub Actions), and AWS ECS/RDS/ElastiCache deployment are all planned — see [Execution Plan](#execution-plan) Sprints 23–26.

---

## Database Schema

Reflects actual SQLAlchemy models (`backend/app/models/`), not an aspirational schema:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    location      VARCHAR,
    role          VARCHAR NOT NULL DEFAULT 'user',   -- 'user' | 'admin'
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Meals (flat schema — no separate restaurants table, no category column;
-- category is derived heuristically at query time from name/description)
CREATE TABLE meals (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR,
    price       FLOAT,
    location    VARCHAR,
    description VARCHAR,
    confidence  FLOAT DEFAULT 100.0,
    image_url   VARCHAR,
    latitude    FLOAT,
    longitude   FLOAT,
    embedding   VECTOR(1536)                        -- Gemini text-embedding-004
);

-- Saved meals (user bookmarks)
CREATE TABLE saved_meals (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
    meal_id    INTEGER REFERENCES meals(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, meal_id)
);

-- Community price reports / AI-agent-found prices (unified table)
CREATE TABLE pending_verifications (
    id               SERIAL PRIMARY KEY,
    meal_id          INTEGER REFERENCES meals(id) ON DELETE CASCADE,
    source           VARCHAR(50) DEFAULT 'community',   -- 'community' | 'web_agent'
    raw_data         JSONB,
    extracted_price  FLOAT NOT NULL,
    confidence       FLOAT DEFAULT 100.0,
    status           VARCHAR(20) DEFAULT 'pending',      -- pending | approved | rejected
    agent_thread_id  VARCHAR(100),
    reported_price   FLOAT,                              -- community-report field
    reporter_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    notes            VARCHAR(2000),
    reporter_name    VARCHAR(100),
    photo_url        VARCHAR,
    created_at       TIMESTAMPTZ DEFAULT now()
);
```

**Note:** `category` does not exist as a column anywhere. Category-based filtering (e.g. in `filter_meals` tool) uses a keyword heuristic against `name`/`description` (`_extract_category` in `services/meal.py`), not a dedicated indexed column. This is a deliberate scope decision, not an oversight — documented in the code comments at the point of use.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Register. `role` is never client-settable. |
| POST | `/auth/login` | — | Rate-limited 5/min. Returns `{ access_token, token_type }` |
| GET | `/auth/me` | JWT | Get current user |

### Meals
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/meals` | — | Paginated list/search. Rate-limited 30/min. |
| GET | `/meals/nearby` | — | PostGIS geo-filtered search |
| GET | `/meals/{id}` | — | Detail: price history (from real approved reports) + AI insight |
| POST | `/meals` | Admin | Create meal |
| POST | `/meals/{id}/save` | JWT | Bookmark a meal |
| DELETE | `/meals/{id}/save` | JWT | Remove bookmark |

### Reports
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/reports` | Optional JWT | Submit price report. Rate-limited 10/min. AI-validated before insert; sanitized via `bleach`. |

### Admin
All admin routes require a JWT whose live DB `role == "admin"`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | Meal/user/report counts, avg confidence |
| GET | `/admin/meals` | Per-meal report count + last-reported timestamp |
| GET | `/admin/reports` | Report list, filterable by `?status=` |
| POST | `/admin/reports/{id}/approve` | Approve → updates meal price, restores confidence |
| POST | `/admin/reports/{id}/reject` | Reject → restores confidence |
| POST | `/admin/reports/bulk-approve` | Bulk approve. Body: `{ ids: [...] }` |

### Agent
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/agent/live-price` | — | SSE stream. Rate-limited 5/min. Query: `?query=` |
| POST | `/agent/resume/{thread_id}` | — | Resume paused HITL LangGraph thread. Body: `{ action: "approve"\|"reject" }` |

### Chat
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/chat` | JWT | SSE stream. Rate-limited 10/min. Body: `{ message, lat?, lng?, thread_id? }` |

---

## Project Structure

Reflects the actual synced tree, not an aspirational layout:

```
Foodly/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/       # meals, reports, admin, auth, users, agent, chat
│   │   ├── core/                 # config, database, cache, rate_limit, security_headers, logging_config
│   │   ├── models/                # User, Meal, SavedMeal, PendingVerification
│   │   ├── schemas/               # Pydantic v2 DTOs (meal, user, report, auth)
│   │   ├── services/              # meal.py, embeddings.py, auth.py
│   │   └── repositories/          # meal.py (DB queries only, no business logic)
│   ├── ai/
│   │   ├── agents/                # price_scraper.py (LangGraph), agents.py (legacy insight)
│   │   ├── chains/                # insight_chain, query_expansion_chain, report_validation_chain, refine_query_chain
│   │   ├── graph/                 # state.py, checkpointer.py, assistant_graph.py
│   │   └── tools/                 # foodly_tools.py, search_tools.py
│   ├── scripts/                   # init_db, seed_islamabad, ingest_meals, generate_embeddings, promote_admin, add_user_role_column
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                   # page.tsx, meals/[id], saved, profile, admin, auth/login
│       ├── components/            # MapPanel.tsx, ChatPanel.tsx, Navbar.tsx
│       └── lib/                   # api.ts, types.ts
├── automation/n8n-workflows/       # report_webhook.json
├── docker-compose.yml              # currently: redis only
├── execution_plan.md
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 with PostGIS and pgvector extensions
- API keys: Google Gemini, Groq, Tavily (all have free tiers)

### 1. Clone
```bash
git clone <repo-url>
cd Foodly
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
# fill in .env values — see Environment Variables below
```

### 3. Database
```bash
cd backend
python scripts/init_db.py
```
This enables `pgvector`, drops, and recreates all tables from the current SQLAlchemy models.

### 4. Seed data (optional but recommended)
```bash
python scripts/seed_islamabad.py
```

### 5. Start backend
```bash
cd backend
python run.py
# or: uvicorn app.main:app --reload --port 8000
```
API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Start frontend
```bash
cd frontend
npm install
npm run dev
```
App: [http://localhost:3000](http://localhost:3000)

### 7. Redis (required for caching)
```bash
docker-compose up redis
```

### 8. Or run both together from repo root
```bash
npm install
npm run dev
```

---

## Environment Variables

`backend/.env` — see `backend/.env.example` for the authoritative template. **`DATABASE_URL` and `SECRET_KEY` are required; the app will not start without them, and `SECRET_KEY` is additionally rejected if it's a known placeholder or under 32 bytes.**

```env
# ── Database (required, no default) ───────────────────────────────
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/foodly_db

# ── Auth (required, no default) ────────────────────────────────────
SECRET_KEY=                     # generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── CORS ────────────────────────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ── AI (required for AI features to function — degrade gracefully if missing) ──
GOOGLE_API_KEY=
GROQ_API_KEY=
TAVILY_API_KEY=

# ── Cache ───────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379

# ── Automation (optional) ──────────────────────────────────────────
N8N_WEBHOOK_URL=
```

| Key | Where to get | Free tier |
|-----|-------------|-----------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) | Yes |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com) | Yes |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com) | Yes — 1,000 searches/month |

---

## Foodly Score Algorithm

```
Foodly Score = (Budget Fit × 0.40) + (Proximity × 0.35) + (Confidence × 0.25)
```

| Component | Formula | Range | Weight |
|-----------|---------|-------|--------|
| Budget Fit | `max(0, 1 − price/budget) × 100` | 0–100 | 40% |
| Proximity | `max(0, 100 − distance_km × 20)` | 0–100 | 35% |
| Confidence | `meal.confidence` | 0–100 | 25% |

**Example:** A PKR 180 biryani (budget PKR 500) at 0.5km with confidence 95:
- Budget Fit = `(1 - 180/500) × 100` = 64
- Proximity = `100 - 0.5×20` = 90
- Confidence = 95
- **Score = 64×0.40 + 90×0.35 + 95×0.25 = 80.85**

---

## Known Issues

Corrected against actual code — replaces a prior version of this table that had gone stale (it previously listed admin auth and CORS as open issues; both are fixed).

| Issue | File | Severity | Notes |
|-------|------|----------|-------|
| Hardcoded DB credential fragment in a log statement | `backend/ai/graph/checkpointer.py` | 🔴 Critical | A literal password-shaped string is used as the redaction target — masking breaks the moment the password rotates, and the fragment itself is committed to git history. Remove the print; rotate the credential if it was ever real. |
| Shared SQLAlchemy `Session` across `ThreadPoolExecutor` threads | `backend/ai/chains/insight_chain.py` (`generate_rag_insight`) | 🔴 High | SQLAlchemy sessions are not thread-safe. Give each of the 3 parallel context-fetch helpers its own `SessionLocal()`. |
| Three overlapping seed/embedding scripts, no documented canonical path | `backend/scripts/ingest_meals.py`, `generate_embeddings.py`, `seed_islamabad.py` | 🟡 Medium | Consolidate or clearly re-scope each. |
| Committed error log with local file paths | `backend/logs/reports_error.log` | 🟡 Medium | Check git history predates the current `.gitignore` rule; scrub if needed. |
| Unrelated npm package shadowing the Python `bleach` sanitizer | root `package.json` | 🟡 Medium | `bleach` is listed as an npm dependency but is unused; the real sanitizer is Python's `bleach==6.1.0`. Remove. |
| JWT stored in `localStorage` | `frontend/src/lib/api.ts` | 🟡 Medium | XSS-vulnerable token storage. Defensible for MVP stage given server-side sanitization elsewhere; flagged for explicit decision at the Sprint 27 security audit rather than left implicit. |
| No `tests/integration/` or `tests/ai/` suites exist | — | 🟡 Gap | Blocking the project's own stated Sprint 1 and Sprint 9 exit criteria. |
| A09 logging — `print()` still used outside auth/reports/admin | various | 🟢 Low | `structlog` migration covers hot paths only so far; full replacement planned. |

---

## Execution Plan

See `execution_plan.md` (v7.0) for the full 30-sprint roadmap, corrected sprint-by-sprint status, and task-level breakdowns for all planned work (personalized feed, multi-agent supervisor, LangSmith, streaming, caching, WebSockets, Kafka, production infra, growth features).

---

## License

Private — Muhammad Haris · Foodly · 2026