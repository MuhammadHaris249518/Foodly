# Foodly

**AI-powered, community-verified food discovery platform for Islamabad & Rawalpindi.**

Foodly helps users find nearby, affordable meals with live price updates, semantic search, GPS filtering, and AI-generated value insights. Built as a production-grade startup MVP targeting a PKR 15M seed round.

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
17. [60-Day Roadmap](#60-day-roadmap)

---

## What It Does

| Feature | Description |
|---------|-------------|
| **Geo-filtered search** | Meals within a configurable radius, sorted by PostGIS distance |
| **Semantic search** | pgvector cosine similarity — understands "student budget lunch" without exact keywords |
| **Live web intelligence** | LangGraph agent searches the web in real time, streams results via SSE |
| **AI value insights** | LangChain + Gemini generates grounded verdict using real sector price data (RAG) |
| **Confidence score system** | Every meal starts at 100%, decays 5pts per pending report, restores on admin approval |
| **Community price reports** | Users submit price updates with optional photo; admin moderates |
| **Human-in-the-loop (HITL)** | Web agent findings pause for admin review via LangGraph `interrupt()` before applying to DB |
| **Conversational assistant** | ReAct agent with DB tools — "find something under PKR 200 near NUST, not biryani" |
| **Personalized feed** | User taste profile via embedding centroid — surfaces meals matching past saves |
| **Saved meals** | Authenticated bookmarks synced to DB |
| **Admin dashboard** | Real-time stats, report queue, moderation, agent controls |

---

## Tech Stack

### Backend (Current)
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | FastAPI | 0.136 |
| Language | Python | 3.11 |
| ORM | SQLAlchemy | 2.0 |
| Database | PostgreSQL + PostGIS + pgvector | 15 |
| Auth | python-jose (JWT HS256) + passlib bcrypt | — |
| AI Orchestration | LangGraph | 1.1 |
| AI Chains | LangChain LCEL | 1.2 |
| LLM — Reasoning | Google Gemini 2.0 Flash | — |
| LLM — Structured Output | Groq llama-3.3-70b-versatile | — |
| Embeddings | Google Gemini text-embedding-004 | 1536-dim |
| Web Search | Tavily Search API | — |
| Real-time | SSE via sse-starlette | — |
| Automation | N8N webhooks | — |
| Server | Uvicorn | — |

### Backend (Planned — Layers 3–6)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Caching | Redis / Upstash | Sub-150ms API responses, semantic response cache |
| Message broker | Apache Kafka | Decouple HTTP handlers from side effects |
| WebSockets | FastAPI native | Live notifications, search suggestions, agent events |
| AI observability | LangSmith | Trace every LangGraph/LangChain call, token cost tracking |
| Async workers | Python asyncio consumers | Notification, cache invalidation, email, scraper workers |
| Containerization | Docker + Docker Compose | Environment parity, one-command startup |
| CI/CD | GitHub Actions | Automated test → build → deploy pipeline |
| Cloud | AWS ECS Fargate + RDS + ElastiCache | Production deployment |
| Monitoring | CloudWatch + Sentry + Prometheus | Structured logs, alerts, error tracking |
| Rate limiting | SlowAPI | Per-IP and per-user endpoint throttling |

### Frontend
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
│  Next.js 16  ·  React Leaflet  ·  Framer Motion  ·  TypeScript     │
│  REST (Axios)  ·  SSE (EventSource)  ·  WebSocket                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / WSS
┌────────────────────────────▼────────────────────────────────────────┐
│                    GATEWAY / LOAD BALANCER                          │
│           AWS ALB  ·  SSL Termination (ACM)  ·  Route 53           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│                    FastAPI  ·  Uvicorn  ·  ECS Fargate              │
│                                                                     │
│  ┌──────────────┐  ┌────────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  REST API    │  │  WebSocket │  │  SSE     │  │  Kafka      │  │
│  │  /api/v1/*   │  │  /api/v1/  │  │  /agent/ │  │  Producer   │  │
│  │              │  │  ws        │  │  live-   │  │             │  │
│  └──────┬───────┘  └─────┬──────┘  │  price   │  └──────┬──────┘  │
│         │                │         └──────────┘         │         │
│  ┌──────▼───────────────────────────────────────────────▼──────┐   │
│  │                     SERVICE LAYER                           │   │
│  │  MealService · AuthService · ReportService · AgentService   │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                   AI WORKFLOW LAYER                         │   │
│  │                                                             │   │
│  │  LangGraph Graphs          LangChain Chains                 │   │
│  │  ├─ price_agent            ├─ insight_chain (RAG)           │   │
│  │  ├─ assistant_graph        ├─ expansion_chain               │   │
│  │  └─ supervisor_graph       ├─ validation_chain              │   │
│  │       (multi-agent)        └─ personalization_chain         │   │
│  │                                                             │   │
│  │  Tools: Tavily · pgvector · DB queries · PostGIS            │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                        DATA LAYER                                   │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  PostgreSQL 15   │  │  Redis       │  │  Apache Kafka         │ │
│  │  ├─ PostGIS      │  │  ├─ Cache    │  │  ├─ report.approved   │ │
│  │  ├─ pgvector     │  │  ├─ Sessions │  │  ├─ meal.price_changed│ │
│  │  └─ Checkpointer │  │  └─ Pub/Sub  │  │  ├─ scrape.job.*      │ │
│  │     (LangGraph   │  │  (suggestions│  │  └─ agent.hitl_*      │ │
│  │      HITL state) │  │   + presence)│  │                       │ │
│  └──────────────────┘  └──────────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                      WORKER LAYER (Kafka Consumers)                 │
│  notification_worker · cache_worker · email_worker · scraper_worker │
│                         hitl_worker                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## AI Architecture

### AI Feature Map

| Feature | Tool | Graph / Chain | Status |
|---------|------|--------------|--------|
| Semantic search embeddings | Gemini `text-embedding-004` + pgvector | — | Live |
| Live price scraper | LangGraph `StateGraph` + Groq + Tavily | `price_agent` | Live (retry broken — Day 9 fix) |
| AI value insight | LangChain LCEL + Gemini | `agents.py` | Live (single-shot — Day 10 RAG upgrade) |
| Grounded RAG insight | LangChain LCEL + pgvector context | `insight_chain` | Day 10 |
| Smart query expansion | LangChain LCEL + Groq | `expansion_chain` | Day 11 |
| AI report validator | LangChain LCEL + Groq | `validation_chain` | Day 12 |
| Human-in-the-loop (HITL) | LangGraph `interrupt()` + PG checkpointer | `price_agent` | Day 13 |
| Conversational assistant | LangGraph ReAct + 5 DB tools | `assistant_graph` | Day 14 |
| Personalized feed | LangChain LCEL + pgvector centroid | `personalization_chain` | Day 15 |
| Nightly enrichment supervisor | LangGraph multi-agent `Send()` | `supervisor_graph` | Day 16 |
| AI observability | LangSmith tracing + eval datasets | — | Day 17 |
| Streaming AI responses | `.astream()` + SSE | all chains | Day 18 |
| Safe fallbacks / circuit breaker | `safe_invoke` wrapper | all | Day 19 |

---

### 1. LangGraph Price Scraper (`price_agent`)
**File:** [backend/ai/agents/price_scraper.py](backend/ai/agents/price_scraper.py)

```
[search_node] → [extract_node] → should_continue()
                                      ├─ "store"  → [store_node] → END   (confidence ≥ 50)
                                      ├─ "retry"  → [retry_node] → search (confidence < 50, iter < 3)
                                      └─ "end"    → END                   (iter ≥ 3)
```

**State:** `AgentState(search_query, search_results, extracted_data, iterations, meal_id, thread_id)`

**LLMs used:**
- `search_node` — Tavily Search API (web retrieval)
- `extract_node` — Groq `llama-3.3-70b` with `with_structured_output(ExtractedPrice)`
- `retry_node` — Groq generates a refined search query when confidence < 50

**Output:** `ExtractedPrice(restaurant_name, meal_name, price_pkr, confidence, source_url)`

**Streamed via SSE** to frontend as `searching → extracting → complete` events.

---

### 2. LangGraph Human-in-the-Loop (`price_agent` + HITL)
**Planned — Day 13**

LangGraph's `interrupt()` pauses the graph at admin review. State is persisted to PostgreSQL via `AsyncPostgresSaver`. Admin resumes via `POST /api/v1/agent/resume/{thread_id}`.

```
web_agent_finds_price
    → validate_price_node
    → human_review_node  ←── PAUSED HERE (interrupt)
    → (admin calls /agent/resume/{thread_id} with "approve"/"reject")
    → apply_price_update
    → notify_reporter
    → END
```

This replaces the disconnected `pending_verifications` REST workflow with a durable, stateful process. The graph survives server restarts because its state is checkpointed in PostgreSQL.

---

### 3. LangGraph Conversational Assistant (`assistant_graph`)
**Planned — Day 14**

A ReAct agent with 5 domain-specific tools:

```python
@tool async def search_nearby_meals(lat, lng, radius_km, max_price) → list[Meal]
@tool async def filter_meals(meals, exclude_category, min_confidence) → list[Meal]
@tool async def get_meal_insight(meal_id) → str
@tool async def get_price_trend(meal_id) → str   # rising | falling | stable
@tool async def semantic_search_meals(query, limit) → list[Meal]
```

Built with `create_react_agent(model, tools, checkpointer)`. Supports multi-turn conversation — the checkpointer persists session context across requests. Streams `thinking → tool_call → tool_result → token → done` events via WebSocket.

---

### 4. LangGraph Multi-Agent Supervisor (`supervisor_graph`)
**Planned — Day 16**

Uses LangGraph's `Send()` API to fan out to 50 parallel price-scraper sub-agents:

```
SELECT top-50 meals
    → supervisor distributes via Send()
    → [price_agent_1, price_agent_2, ..., price_agent_50]  ← parallel
    → aggregator_node collects results
    → batch insert to pending_verifications
    → notify admins via WebSocket
    → END
```

Runs nightly at 2am PKT via APScheduler. HTTP server unaffected during the run.

---

### 5. LangChain RAG Insight Chain (`insight_chain`)
**Planned — Day 10** — replaces the current single-shot prompt in `agents.py`

```python
insight_chain = (
    RunnableParallel({
        "similar_meals":  retrieve_similar_meals,   # pgvector top-5 same category
        "sector_stats":   fetch_sector_stats,       # avg/min/max price in sector
        "price_history":  fetch_price_history,      # last 10 approved reports
        "meal":           RunnablePassthrough()
    })
    | build_grounded_prompt
    | ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    | InsightResponseParser          # → InsightResponse(verdict, summary, tip, price_percentile)
)
```

**Current problem:** `agents.py:generate_value_insight` sends only name/price/location to the model with no market context. It cannot say "this is cheaper than 80% of similar meals in F-7" because it has no data about other meals.

---

## Security Architecture

### Authentication & Authorization

**JWT (HS256)**
- Payload: `{ sub: user_id, role: user.role, jti: uuid4(), exp: now+7d }`
- `SECRET_KEY` minimum 32 bytes, stored in `.env` / AWS Secrets Manager
- Token revocation via Redis: `POST /auth/logout` adds `jti` to a Redis revocation set with matching TTL
- Every protected route validates token + checks revocation set via `Depends(get_current_user)`

**Admin access**
- Current: `X-Admin-Secret` header (simple shared secret)
- Planned Day 11: migrate to `role=admin` JWT claim with `Depends(require_role("admin"))`

**Password hashing**
- bcrypt via `passlib`, cost factor 12
- Register returns user object — never returns `password_hash`
- Login returns same error message for wrong email and wrong password (prevents user enumeration)

---

### OWASP Top 10 Hardening (Planned — Day 11)

| Threat | Mitigation |
|--------|-----------|
| **A01 Broken Access Control** | Role-based JWT claims, admin routes reject non-admin tokens with `403` |
| **A02 Cryptographic Failures** | bcrypt cost 12, JWT HS256 with 32-byte minimum secret, HTTPS enforced |
| **A03 SQL Injection** | SQLAlchemy ORM only — zero raw string interpolation in queries. Test: `'; DROP TABLE meals; --` returns empty results, not 500 |
| **A04 Insecure Design** | Service layer enforced — no business logic in route handlers |
| **A05 Security Misconfiguration** | Secrets via AWS Secrets Manager in prod, never in Docker images or `.yml` files |
| **A07 Auth Failures** | Rate limit `/auth/login` to 5 req/min per IP; same error message for wrong email vs password |
| **A09 Logging Failures** | Structured JSON logs — every request logged with `user_id`, `endpoint`, `latency_ms`, `status_code` |

**Security headers middleware** (all responses):
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

**XSS prevention:** `bleach.clean()` applied to all free-text inputs (meal names, report notes) before DB write.

---

### Rate Limiting (Planned — Day 11)

Implemented via `slowapi`:

| Endpoint | Limit | Scope |
|----------|-------|-------|
| `POST /auth/login` | 5 req/min | Per IP |
| `GET /meals/search` | 30 req/min | Per user (auth) / Per IP (anon) |
| `GET /meals/nearby` | 60 req/min | Per user |
| `POST /reports` | 10 req/min | Per user |
| `GET /agent/live-price` | 5 req/min | Per user |
| `POST /chat` | 10 req/min | Per user (AI is expensive) |
| Global | 100 req/min | Per IP |

All rate-limit violations return `429 Too Many Requests` with `Retry-After` header.

---

### Token Revocation Flow

```
Client calls POST /auth/logout
    → Extract jti from JWT
    → Redis: SET revoked:{jti} "1" EX {remaining_ttl_seconds}
    → Return 200

Next request with same token:
    → Decode JWT → get jti
    → Redis GET revoked:{jti}
    → If exists → return 401 "token revoked"
    → If not → proceed normally
```

---

## Caching Architecture (Redis)

**Planned — Days 10 & 22**

### Cache Key Strategy

| Data | Redis Key | TTL | Invalidated By |
|------|-----------|-----|----------------|
| Search results | `search:{sha256(query+filters)}` | 15 min | Meal create/update |
| Nearby results | `nearby:{lat}:{lng}:{radius}:{filters_hash}` | 5 min | Meal create/update |
| AI insight | `insight:{meal_id}:{price_cents}` | 24 hr | Price change (key changes with price) |
| Personalized feed | `feed:{user_id}:{location_hash}` | 10 min | User saves new meal |
| Query expansion | `expansion:{sha256(query)}` | 1 hr | Never (terms are stable) |
| Report validation | `validation:{meal_id}:{price}` | 6 hr | Never |
| Admin stats | `admin:stats` | 60 sec | Any report action |
| Online user count | `foodly:online_users` (counter) | Live | WS connect/disconnect |
| Revoked JWTs | `revoked:{jti}` | Token TTL | Logout |
| WS sessions | `ws:session:{user_id}` | 30 min | Disconnect |

### Semantic Cache (Chat Assistant)

Similar chat queries return cached responses without hitting Groq:

```
User query → embed → query_vec
    → Redis: find cached key where cosine_dist(cached_vec, query_vec) < 0.1
    → If found: return cached response (X-Cache: HIT)
    → If not: run assistant → cache response + embedding
```

### Cache Response Header

All cached endpoints return `X-Cache: HIT` or `X-Cache: MISS` for debugging and demo visibility.

---

## Real-time Architecture (WebSockets)

**Planned — Days 27–30**

### Connection Manager

```python
class ConnectionManager:
    active: dict[int, list[WebSocket]]  # user_id → [ws1, ws2, ...]  (multi-tab support)

    async def connect(ws: WebSocket, user_id: int)
    async def disconnect(ws: WebSocket, user_id: int)
    async def send_to_user(user_id: int, message: dict)
    async def send_to_admins(message: dict)
    async def broadcast(message: dict)
```

### Event Types

| Event Type | Direction | Trigger | Receiver |
|-----------|-----------|---------|---------|
| `connected` | Server → Client | Successful WS auth | User |
| `report_approved` | Server → Client | Admin approves report | Reporter |
| `report_rejected` | Server → Client | Admin rejects report | Reporter |
| `price_changed` | Server → Client | Report approved | All users who saved that meal |
| `new_report` | Server → Client | User submits report | All admin connections |
| `agent_needs_review` | Server → Client | LangGraph hits HITL interrupt | All admin connections |
| `agent_started` | Server → Client | Scrape job begins | Requesting user |
| `agent_found` | Server → Client | Agent finds a price | Requesting user |
| `search_suggest` | Client → Server | User types (debounced 300ms) | — |
| `suggestions` | Server → Client | Embedding search complete | User |
| `chat_message` | Client → Server | User sends chat | — |
| `token` | Server → Client | LLM streaming token | User |
| `ping` / `pong` | Both | Heartbeat every 30s | Both |

### Authentication

WebSocket auth via JWT query param (WebSocket protocol has no standard headers):
```
ws://host/api/v1/ws?token=eyJhbGci...
```
Invalid JWT → connection closed with code `4001` immediately.

### Frontend Auto-Reconnect

```typescript
// hooks/useWebSocket.ts
const delays = [1000, 2000, 4000, 8000, 16000, 30000]  // exponential backoff, max 30s
```

---

## Event-driven Architecture (Kafka)

**Planned — Days 32–36**

### Why Kafka

Before Kafka, every HTTP handler is responsible for its own side effects synchronously:

```python
# BEFORE — blocks HTTP response (200–500ms of side effects):
async def approve_report(report_id):
    await db.update(...)                     # 10ms
    await manager.send_to_user(...)          # 50ms  ← WS delivery
    await cache.invalidate(...)              # 20ms  ← Redis
    await send_email(...)                    # 300ms ← Resend API
    await langsmith.log(...)                 # 80ms
    return response                          # total: ~460ms
```

After Kafka, the HTTP handler emits one event and returns immediately:

```python
# AFTER — HTTP returns in < 50ms:
async def approve_report(report_id):
    await db.update(...)                     # 10ms
    await kafka.emit("report.approved", ...) # 5ms   ← async, non-blocking
    return response                          # total: ~15ms
```

Side effects run in separate worker processes consuming from Kafka topics.

---

### Topics

| Topic | Partitions | Consumers | Payload |
|-------|-----------|-----------|---------|
| `report.approved` | 4 | notification_worker, cache_worker, email_worker | `{ report_id, meal_id, reporter_id, new_price, old_price, correlation_id }` |
| `report.rejected` | 2 | notification_worker, cache_worker | `{ report_id, meal_id, reporter_id, correlation_id }` |
| `meal.price_changed` | 4 | notification_worker, cache_worker | `{ meal_id, old_price, new_price, correlation_id }` |
| `scrape.job_requested` | 2 | scraper_worker | `{ meal_id, search_query, job_id, correlation_id }` |
| `scrape.job_completed` | 2 | verification_worker | `{ job_id, meal_id, result, confidence, correlation_id }` |
| `agent.hitl_decision` | 2 | hitl_worker | `{ thread_id, decision, admin_id, correlation_id }` |

### Worker Services

| Worker | Consumes | Does |
|--------|---------|------|
| `notification_worker` | `report.*`, `meal.price_changed` | Pushes WebSocket events to users/admins |
| `cache_worker` | `report.*`, `meal.price_changed` | Invalidates Redis keys |
| `email_worker` | `report.approved` | Sends Resend confirmation email to reporter |
| `scraper_worker` | `scrape.job_requested` | Runs LangGraph price agent asynchronously |
| `verification_worker` | `scrape.job_completed` | Inserts results to `pending_verifications`, notifies admin |
| `hitl_worker` | `agent.hitl_decision` | Resumes paused LangGraph graph via checkpointer |

### Correlation IDs

Every event carries a `correlation_id: uuid4()`. Every log line for that event's side effects includes it. Enables full end-to-end trace: HTTP request → Kafka event → consumer → side effect.

### Dead-Letter Queues

Every topic has a `.dlq` companion (`report.approved.dlq`). If a consumer throws 3 times on the same message, it is routed to the DLQ and an alert fires. Prevents poison-pill messages from blocking the queue forever.

---

## Infrastructure & DevOps

### Docker Compose (Full Stack)

**Planned — Day 39**

```yaml
services:
  postgres:      # PostgreSQL 15 with PostGIS + pgvector
  redis:         # Redis 7 (cache + pub/sub + session store)
  zookeeper:     # Kafka dependency
  kafka:         # Confluent 7.5 (event broker)
  kafka-ui:      # Kafka UI at localhost:8080
  backend:       # FastAPI (multi-stage image, < 200MB)
  frontend:      # Next.js standalone output
  notification_worker:
  cache_worker:
  email_worker:
  scraper_worker:
  hitl_worker:
```

Single command to start everything:
```bash
docker-compose up --build
```

### CI/CD Pipeline (GitHub Actions)

**Planned — Day 40**

```
PR opened / push to any branch
    └─ ci.yml
        ├─ Start postgres + redis (docker services)
        ├─ Run alembic migrations
        ├─ pytest --cov=app (fail if coverage < 70%)
        ├─ ruff check . (Python linting)
        ├─ mypy app/ (type checking)
        └─ eslint frontend/src/ (TypeScript linting)

Merge to main (CI passes)
    └─ deploy.yml
        ├─ Build Docker image (multi-stage)
        ├─ Push to AWS ECR (tagged: SHA + latest)
        ├─ Update ECS service (rolling deploy, zero downtime)
        └─ Run alembic upgrade head
```

Branch protection: PRs cannot merge if CI fails.

### AWS Production Infrastructure

**Planned — Day 41**

```
Route 53
  api.foodly.pk → ALB → ECS Fargate (backend + workers)
  foodly.pk     → Vercel (frontend CDN)

AWS Services:
  ├─ ECS Fargate        — backend service + 5 worker services (0.5 vCPU / 1GB each)
  ├─ RDS PostgreSQL 15  — private subnet, db.t3.micro, 7-day automated backups
  ├─ ElastiCache Redis  — private subnet, cache.t3.micro
  ├─ MSK / self-hosted Kafka — event broker
  ├─ ECR               — Docker image registry
  ├─ ALB               — HTTPS termination, health checks on /health
  ├─ ACM               — SSL certificate for api.foodly.pk
  └─ Secrets Manager   — all API keys and DB credentials (never in task definitions)
```

### Observability Stack

**Planned — Day 42**

| Signal | Tool | What's Tracked |
|--------|------|---------------|
| **Logs** | structlog → CloudWatch | `{ timestamp, level, service, correlation_id, endpoint, latency_ms, status_code, user_id }` |
| **Metrics** | Prometheus + CloudWatch | p50/p95/p99 per endpoint, active WS connections, Kafka consumer lag, AI call latency |
| **Errors** | Sentry | Unhandled exceptions with stack trace, user context, request data |
| **AI traces** | LangSmith | Every LangGraph/LangChain call — inputs, outputs, latency, token count, cost |
| **Alerts** | CloudWatch Alarms | p95 > 500ms (5min), error rate > 1%, RDS CPU > 80% → email/PagerDuty |
| **Dashboards** | CloudWatch | p95 per endpoint, error rate, WS connections, Kafka lag, AI call costs |

---

## Database Schema

```sql
-- Installed extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    location      VARCHAR,
    karma_score   INTEGER DEFAULT 0,          -- increases on approved reports
    role          VARCHAR DEFAULT 'user',     -- 'user' | 'admin'
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Restaurants
CREATE TABLE restaurants (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR NOT NULL,
    address    VARCHAR,
    sector     VARCHAR,                       -- e.g. F-7, G-9, Blue Area
    location   GEOGRAPHY(POINT, 4326),        -- PostGIS point for geo-queries
    is_featured BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Meals (core entity)
CREATE TABLE meals (
    id               SERIAL PRIMARY KEY,
    restaurant_id    INTEGER REFERENCES restaurants(id),
    name             VARCHAR NOT NULL,
    description      VARCHAR,
    price            FLOAT NOT NULL,
    category         VARCHAR,                 -- biryani | karahi | fast food | ...
    image_url        VARCHAR,
    confidence_score FLOAT DEFAULT 100.0,     -- decays on reports, restores on approval
    is_featured      BOOLEAN DEFAULT false,
    embedding        VECTOR(1536),            -- Gemini text-embedding-004
    -- Legacy flat columns (current implementation — to be migrated)
    location         VARCHAR,
    latitude         FLOAT,
    longitude        FLOAT,
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now()
);

-- Saved meals (user bookmarks)
CREATE TABLE saved_meals (
    user_id  INTEGER REFERENCES users(id) ON DELETE CASCADE,
    meal_id  INTEGER REFERENCES meals(id) ON DELETE CASCADE,
    saved_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, meal_id)
);

-- Community price reports
CREATE TABLE pending_verifications (
    id                  SERIAL PRIMARY KEY,
    meal_id             INTEGER REFERENCES meals(id) ON DELETE CASCADE,
    reported_price      FLOAT NOT NULL,
    notes               VARCHAR,
    reporter_name       VARCHAR,
    reporter_id         INTEGER REFERENCES users(id),   -- null for anonymous
    photo_url           VARCHAR,
    status              VARCHAR DEFAULT 'pending',       -- pending | approved | rejected
    ai_validation_score INTEGER,                        -- 0-100 from validation_chain
    agent_thread_id     VARCHAR,                        -- LangGraph HITL thread ID
    created_at          TIMESTAMPTZ DEFAULT now()
);
```

**Performance indexes:**
```sql
-- Spatial (geo-search) — uses GiST
CREATE INDEX restaurants_location_gix ON restaurants USING GIST(location);
CREATE INDEX meals_location_gix ON meals
    USING GIST(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));

-- Vector (semantic search) — uses HNSW
CREATE INDEX ON meals USING hnsw (embedding vector_cosine_ops);

-- Relational (filter + sort)
CREATE INDEX ON meals(category, price);
CREATE INDEX ON pending_verifications(meal_id, status);
CREATE INDEX ON saved_meals(user_id);
CREATE INDEX ON meals(restaurant_id);
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Auth
| Method | Endpoint | Auth | Body | Description |
|--------|----------|------|------|-------------|
| POST | `/auth/register` | — | `{ email, password }` | Register. Returns `{ id, email }` |
| POST | `/auth/login` | — | `{ email, password }` | Returns `{ access_token, token_type }` |
| GET | `/auth/me` | JWT | — | Get current user |
| POST | `/auth/logout` | JWT | — | Revoke JWT via Redis |

### Meals
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/meals` | — | Paginated list. Query: `budget`, `search`, `skip`, `limit` |
| GET | `/meals/nearby` | — | Geo-filtered. Query: `lat`, `lng`, `radius_km`, `budget`, `search` |
| GET | `/meals/search` | — | Semantic search. Query: `q` |
| GET | `/meals/{id}` | — | Detail: price history + AI insight |
| GET | `/meals/{id}/insight` | — | AI insight only (cached 24h) |
| GET | `/meals/{id}/insight/stream` | — | Streaming AI insight (SSE) |
| POST | `/meals` | Admin | Create meal |
| PUT | `/meals/{id}` | Admin | Update meal |
| DELETE | `/meals/{id}` | Admin | Soft delete |
| POST | `/meals/{id}/save` | JWT | Toggle bookmark |

### Reports
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/reports` | — | Submit price report (form: `meal_id`, `reported_price`, `notes?`, `photo?`) |
| GET | `/meals/{id}/reports` | — | Price history (approved reports only) |

### Admin
> Header: `X-Admin-Secret: {ADMIN_SECRET}`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | Total meals, report counts, avg confidence |
| GET | `/admin/reports` | Report list. Query: `?status=pending` |
| POST | `/admin/reports/{id}/approve` | Approve → update price, restore confidence |
| POST | `/admin/reports/{id}/reject` | Reject → restore confidence |
| POST | `/admin/reports/bulk-approve` | Bulk approve. Body: `{ ids: [1,2,3] }` |
| GET | `/admin/agent/pending` | LangGraph threads paused at HITL node |
| POST | `/admin/agent/enrichment` | Trigger nightly supervisor agent manually |

### Agent
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/agent/live-price` | — | SSE stream. Query: `?query=biryani` |
| POST | `/agent/resume/{thread_id}` | Admin | Resume HITL LangGraph thread |
| GET | `/agent/jobs/{job_id}` | — | Poll scrape job status (Redis-backed) |

### Chat
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/chat` | JWT | Conversational assistant. Body: `{ message, lat, lng, thread_id? }` |

### WebSocket
| Endpoint | Auth | Description |
|----------|------|-------------|
| `ws://host/api/v1/ws?token=JWT` | JWT query param | Multiplexed: chat + notifications + agent events |

---

## Project Structure

```
Foodly/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── meals.py              # CRUD, geo-search, semantic search, AI insight
│   │   │   ├── reports.py            # Community report submission + photo upload
│   │   │   ├── admin.py              # Stats, moderation, bulk actions, agent controls
│   │   │   ├── auth.py               # Register, login, logout (JWT revocation)
│   │   │   ├── users.py              # Profile, saved meals, personalized feed
│   │   │   ├── agent.py              # LangGraph SSE + HITL resume + job status
│   │   │   ├── chat.py               # Conversational assistant WebSocket/HTTP
│   │   │   └── ws.py                 # WebSocket connection + ConnectionManager
│   │   ├── core/
│   │   │   ├── config.py             # pydantic-settings — all secrets from .env
│   │   │   ├── database.py           # SQLAlchemy async engine + session
│   │   │   ├── security.py           # JWT create/decode, bcrypt, token revocation
│   │   │   ├── cache.py              # Redis get/set/invalidate helpers
│   │   │   ├── websocket_manager.py  # ConnectionManager singleton
│   │   │   └── kafka_producer.py     # async emit() helper
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic v2 request/response DTOs
│   │   ├── services/                 # Business logic (no DB calls, no HTTP)
│   │   └── repositories/             # DB queries only (no logic)
│   │
│   ├── ai/
│   │   ├── agents/
│   │   │   ├── price_scraper.py      # LangGraph StateGraph (search → extract → store)
│   │   │   └── agents.py             # LangChain insight chain (Gemini)
│   │   ├── chains/
│   │   │   ├── insight_chain.py      # RAG insight (pgvector context + Gemini)
│   │   │   ├── expansion_chain.py    # Query expansion (Groq)
│   │   │   ├── validation_chain.py   # Report validation (Groq)
│   │   │   └── personalization_chain.py
│   │   ├── graphs/
│   │   │   ├── assistant_graph.py    # ReAct agent with DB tools
│   │   │   └── supervisor_graph.py   # Multi-agent nightly enrichment
│   │   ├── tools/
│   │   │   ├── search_tools.py       # Tavily web search
│   │   │   └── foodly_tools.py       # DB-backed LangChain tools (search, filter, insight)
│   │   └── state/
│   │       └── base.py               # AgentState TypedDict + output schemas
│   │
│   ├── workers/
│   │   ├── notification_worker.py    # Kafka consumer → WebSocket push
│   │   ├── cache_worker.py           # Kafka consumer → Redis invalidation
│   │   ├── email_worker.py           # Kafka consumer → Resend email
│   │   ├── scraper_worker.py         # Kafka consumer → LangGraph price agent
│   │   ├── verification_worker.py    # Kafka consumer → pending_verifications insert
│   │   └── hitl_worker.py            # Kafka consumer → resume LangGraph checkpoint
│   │
│   ├── scripts/
│   │   ├── seed_islamabad.py         # Seed 200+ real Islamabad restaurants
│   │   └── embed_all_meals.py        # Batch-generate embeddings for all meals
│   │
│   ├── tests/
│   │   ├── integration/              # pytest + httpx.AsyncClient
│   │   └── ai/                       # LangGraph/LangChain integration tests
│   │
│   ├── docs/
│   │   ├── benchmarks.md             # p95 latency before/after each layer
│   │   ├── ai_architecture.md        # ASCII diagrams of all AI workflows
│   │   ├── event_topology.md         # Kafka topic → consumer map
│   │   └── indexes.md                # All DB indexes with justification
│   │
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx              # Homepage: search, map, meal cards, AI panel
│       │   ├── meals/[id]/page.tsx   # Detail: price history, AI insight, report button
│       │   ├── meals/[id]/report/    # Price report form
│       │   ├── saved/                # Saved meals
│       │   ├── profile/              # User profile
│       │   └── admin/                # Admin dashboard
│       ├── components/
│       │   ├── MapPanel.tsx          # React Leaflet with click-to-select
│       │   └── Navbar.tsx
│       └── hooks/
│           ├── useWebSocket.ts       # Auto-reconnect WS hook
│           └── useSSE.ts             # Progressive SSE token rendering
│
├── .github/workflows/
│   ├── ci.yml                        # Test + lint on every PR
│   └── deploy.yml                    # Build + push ECR + update ECS on main
│
├── docker-compose.yml                # Full stack (dev)
├── docker-compose.prod.yml           # Production overrides
├── execution_plan.md                 # 60-day engineering sprint plan
└── README.md
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15 with PostGIS and pgvector extensions
- API keys: Google Gemini, Groq, Tavily (all have free tiers — see table below)

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
# fill in .env values
```

### 3. Database
```bash
psql -U postgres -c "CREATE DATABASE foodly_db;"
psql -U postgres -d foodly_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d foodly_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create tables from ORM models
cd backend
python -c "
from app.core.database import Base, engine
from app.models.meal import Meal
from app.models.user import User
from app.models.saved_meal import SavedMeal
from app.models.pending_verification import PendingVerification
Base.metadata.create_all(bind=engine)
print('All tables created.')
"
```

### 4. Start backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Start frontend
```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000)

### 6. Full stack with Docker (when available — Day 39)
```bash
docker-compose up --build
# All services start: Postgres, Redis, Kafka, Backend, Workers, Frontend
```

---

## Environment Variables

`backend/.env`:

```env
# ── Database ──────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/foodly_db

# ── Auth ──────────────────────────────────────────────────────────
SECRET_KEY=your-minimum-32-character-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── Admin ─────────────────────────────────────────────────────────
ADMIN_SECRET=your-admin-dashboard-password

# ── AI — Google Gemini (embeddings + RAG insight) ─────────────────
GOOGLE_API_KEY=AIza...

# ── AI — Groq (LangGraph structured extraction, expansion, validator)
GROQ_API_KEY=gsk_...

# ── AI — Tavily (web search inside LangGraph agent) ───────────────
TAVILY_API_KEY=tvly-...

# ── AI — LangSmith (tracing + eval — planned Day 17) ─────────────
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=foodly-production

# ── Cache (planned Day 22) ────────────────────────────────────────
REDIS_URL=redis://localhost:6379

# ── Events (planned Day 32) ───────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# ── Email (planned Day 34) ────────────────────────────────────────
RESEND_API_KEY=re_...

# ── Automation (optional) ─────────────────────────────────────────
N8N_WEBHOOK_URL=
```

| Key | Where to get | Free tier |
|-----|-------------|-----------|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) | Yes — generous |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com) | Yes — very fast, free |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com) | Yes — 1,000 searches/month |
| `LANGCHAIN_API_KEY` | [LangSmith](https://smith.langchain.com) | Yes — up to 5K traces/month |
| `RESEND_API_KEY` | [Resend](https://resend.com) | Yes — 3,000 emails/month |

---

## Foodly Score Algorithm

Every search result is ranked by a weighted composite score:

```
Foodly Score = (Budget Fit × 0.40) + (Proximity × 0.35) + (Confidence × 0.25)
```

| Component | Formula | Range | Weight |
|-----------|---------|-------|--------|
| Budget Fit | `max(0, 1 − price/budget) × 100` | 0–100 | 40% |
| Proximity | `max(0, 100 − distance_km × 20)` | 0–100 | 35% |
| Confidence | `meal.confidence_score` | 0–100 | 25% |

**Example:** A PKR 180 biryani (budget PKR 500) at 0.5km with confidence 95:
- Budget Fit = `(1 - 180/500) × 100` = 64
- Proximity = `100 - 0.5×20` = 90
- Confidence = 95
- **Score = 64×0.40 + 90×0.35 + 95×0.25 = 25.6 + 31.5 + 23.75 = 80.85**

---

## Known Issues

| Issue | File | Severity | Planned Fix |
|-------|------|----------|-------------|
| Price history is `random.uniform` (fake data) | [meals.py:134](backend/app/api/endpoints/meals.py) | Critical | Day 6 — replace with real approved reports |
| LangGraph retry branch is dead code (always returns `"end"`) | [price_scraper.py:53](backend/ai/agents/price_scraper.py) | High | Day 9 — fix conditional edge |
| AI insight uses `ThreadPoolExecutor` (not async-safe) | [meals.py:149](backend/app/api/endpoints/meals.py) | High | Day 8 — replace with `asyncio.wait_for()` |
| CORS allows all origins (`"*"`) | [main.py:12](backend/app/main.py) | Medium | Day 11 — restrict to frontend origin |
| No JWT auth on report submission (anonymous allowed) | [reports.py](backend/app/api/endpoints/reports.py) | Medium | Day 11 — add optional JWT, track reporter |
| Admin auth is a shared secret header, not role-based JWT | [admin.py:13](backend/app/api/endpoints/admin.py) | Medium | Day 11 — migrate to `role=admin` JWT claim |
| Price scraper never writes to DB (only prints) | [price_scraper.py](backend/ai/agents/price_scraper.py) | High | Day 9 — add `store_node` to graph |
| AI insight prompt has no market context | [agents.py:17](backend/ai/agents/agents.py) | Medium | Day 10 — RAG chain upgrade |

---

## 60-Day Roadmap

Full plan: [execution_plan.md](execution_plan.md)

| Layer | Days | Focus |
|-------|------|-------|
| **1 — Monolith MVP** | 1–8 | Clean API · DB schema · PostGIS · pgvector · auth · confidence system |
| **2 — AI Workflows** | 9–20 | LangGraph retry fix · RAG insight · query expansion · report validator · HITL · ReAct assistant · personalized feed · multi-agent supervisor · LangSmith · streaming |
| **3 — Performance** | 21–26 | Redis caching · query optimization · OWASP security · rate limiting |
| **4 — Real-time** | 27–31 | WebSockets · live notifications · agent events · search suggestions |
| **5 — Event-driven** | 32–38 | Kafka setup · decouple HTTP handlers · 5 async workers · DLQ |
| **6 — Production** | 39–50 | Docker Compose · GitHub Actions CI/CD · AWS ECS/RDS · CloudWatch · Sentry · LangSmith prod · load testing |
| **7 — Growth** | 51–60 | Analytics · monetization (featured listings) · viral features · investor metrics dashboard |

---

## License

Private — Muhammad Haris · Foodly · 2026
