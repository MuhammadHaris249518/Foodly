# Foodly — 30-Sprint Production Engineering Plan

**Version:** 6.0 · July 2026 (supersedes v5.0 day-based plan)
**Author:** Muhammad Haris
**Target:** PKR 15M / USD 50K Seed Round
**Structure change:** 60 days → 30 sprints. Each sprint = roughly 2 days of the old plan (3–5 hrs/day), but sprint length is not fixed — a sprint ends when its KPI is met, not when a clock runs out.
**Why this changed:** The day-based plan assumed strictly sequential, from-scratch work. In practice, work has happened out of order (security hardening was pulled forward, several Day 9–13 AI fixes were completed early), and the day-based plan's "Current Codebase Baseline" table had gone stale relative to the real repo. This version reflects actual current state and reorganizes remaining work into sprints sized by effort, not calendar days.

---

## Legend

- ✅ **DONE** — verified complete against the actual codebase
- 🔶 **PARTIAL** — some sub-tasks done, gap remains
- ⬜ **TODO** — not started

---

## Sprint Map (30 Sprints Total)

| Sprint | Layer | Focus | Status |
|--------|-------|-------|--------|
| 1 | Foundation | Layer 1 verification + close-out | 🔶 |
| 2 | Security | Finish OWASP hardening (rate limiting, headers, XSS, logging) | 🔶 |
| 3 | AI | Conversational assistant (ReAct + tools) | ⬜ |
| 4 | AI | Personalized feed | ⬜ |
| 5 | AI | Nightly enrichment supervisor (multi-agent) | ⬜ |
| 6 | AI | LangSmith observability | ⬜ |
| 7 | AI | Streaming responses (SSE alignment) | ⬜ |
| 8 | AI | Error handling + fallback audit (`safe_invoke`) | ⬜ |
| 9 | AI | Layer 2 checkpoint — AI eval + integration tests | ⬜ |
| 10 | Performance | Query optimization + indexing | ⬜ |
| 11 | Performance | Redis caching layer | ⬜ |
| 12 | Performance | AI response caching (semantic cache, token savings) | ⬜ |
| 13 | Performance | Layer 3 benchmark + full test suite cleanup | ⬜ |
| 14 | Real-time | WebSocket server + connection manager | ⬜ |
| 15 | Real-time | Live price/report notifications | ⬜ |
| 16 | Real-time | AI agent events over WebSocket | ⬜ |
| 17 | Real-time | Search suggestions + presence + WS load test | ⬜ |
| 18 | Event-driven | Kafka setup + topics | ⬜ |
| 19 | Event-driven | Decouple HTTP handlers via events | ⬜ |
| 20 | Event-driven | Event consumers (workers) | ⬜ |
| 21 | Event-driven | AI agent pipeline via Kafka | ⬜ |
| 22 | Event-driven | Correlation IDs + DLQ + Layer 5 checkpoint | ⬜ |
| 23 | Production | Perf audit post-event layer + Docker Compose | ⬜ |
| 24 | Production | CI/CD pipeline | ⬜ |
| 25 | Production | AWS infrastructure | ⬜ |
| 26 | Production | Structured logging/metrics + production load test | ⬜ |
| 27 | Production | Security audit + AI cost optimization | ⬜ |
| 28 | Production | Final integration test + demo flow | ⬜ |
| 29 | Growth | Analytics + monetization | ⬜ |
| 30 | Growth | Viral features + A/B testing + investor metrics + polish | ⬜ |

---

## SPRINT 1 — Foundation Verification & Close-Out

**Status:** 🔶 Most of this was built in earlier out-of-order work; this sprint is an audit, not new construction.

**Already confirmed done:**
- Service layer pattern (Route → Service → Repository) — `MealRepository`, `MealService` exist and are used
- JWT auth (register/login/me/logout), bcrypt cost 12
- Role-based admin authorization (`require_admin`, `role` column, `promote_admin.py`) — built in this engagement
- PostGIS geo-search (`/nearby`), pgvector semantic search, Foodly Score
- Community price reports + confidence decay/restore system
- Admin stats/reports API, 200+ seeded real Islamabad/Rawalpindi meals with embeddings
- CORS whitelist (env-driven, replaces wildcard) — built in this engagement
- Fail-fast secrets config (`SECRET_KEY`/`DATABASE_URL` required, no insecure defaults) — built in this engagement

**Remaining gap (must verify before closing this sprint):**
1. Confirm `random.uniform` fake price history is fully removed from `meals.py` — run `grep -rn "random" backend/app/api/endpoints/meals.py`. If any instance remains, remove and confirm `price_history` comes only from real approved `pending_verifications` rows.
2. Confirm `ThreadPoolExecutor` is gone from all AI call paths — `grep -rn "ThreadPoolExecutor" backend/`. (Known remaining instance: `generate_rag_insight`'s parallel context-fetch — flagged in the insight chain fix as a *different*, lower-priority thread-safety issue, not the same bug; decide whether to fix now or defer to Sprint 10.)
3. `pytest tests/integration/` — confirm it exists and passes. If it doesn't exist yet, this sprint must create it (auth lifecycle, meals CRUD, geo-search, semantic search, reports, admin — one happy path + one edge case each).
4. `docs/benchmarks.md` — baseline latencies documented for `/nearby`, `/search`, `/meals/{id}`.

**KPI:** Zero fake data, zero unsafe threading in AI paths, one passing integration test suite, documented baseline latencies.

**DoD:**
- `grep -r "random.uniform" backend/app/` → 0 matches
- `pytest tests/integration/` → 0 failures
- `docs/benchmarks.md` committed with real numbers

---

## SPRINT 2 — Finish OWASP Hardening (Immediate Next Task)

**Status:** 🔶 — A01 (auth), A02/A05 (secrets, CORS) done. A03 (SQLi) already safe by construction (SQLAlchemy ORM throughout). A07, A09, and rate limiting remain.

**Tasks:**
1. **Rate limiting (`slowapi`):**
   - Global: 100 req/min per IP
   - `/auth/login`: 5 req/min per IP (brute-force protection — highest priority gap right now)
   - `/meals/search`: 30 req/min per user/IP
   - `/reports`: 10 req/min per user
   - `/chat`, `/agent/live-price`: 5–10 req/min per user (AI cost protection)
   - `429` responses include `Retry-After` header
2. **Security headers middleware** (applies to every response):
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Content-Security-Policy: default-src 'self'`
   - `Referrer-Policy: strict-origin-when-cross-origin`
3. **XSS sanitization:** `bleach.clean()` on all free-text inputs before DB write — specifically `reports.py`'s `notes` and `reporter_name` fields (currently unsanitized).
4. **A09 — structured logging (start here, finish in Sprint 26):** introduce `structlog` for at least the request/response cycle — `{ timestamp, level, endpoint, latency_ms, status_code, user_id }` per request. Full replacement of every `print()` is Sprint 26's job; this sprint just gets the pattern established on the hot paths (auth, reports, admin).

**KPI:** No unauthenticated brute-force path, no reflected/stored XSS via report fields, all responses carry security headers.

**DoD:**
- 6th `/auth/login` attempt in 1 min from same IP → `429`
- `curl -I` any endpoint → all 5 security headers present
- Submit a report with `<script>` in `notes` → stored value is sanitized, not executable
- At least `auth.py` and `reports.py` emit structured JSON logs

---

## SPRINT 3 — Conversational Food Assistant (ReAct + Tools)

**Status:** ⬜ — not yet built. `agent.py` currently only exposes the price-scraper SSE + HITL resume; there is no `/chat` endpoint or ReAct graph.

**Tasks:**
1. `ai/tools/foodly_tools.py` — define as LangChain `@tool` functions:
   - `search_nearby_meals(lat, lng, radius_km, max_price)`
   - `filter_meals(meals, exclude_category, min_confidence)`
   - `get_meal_insight(meal_id)` — reuses `generate_rag_insight`
   - `get_price_trend(meal_id)` — rising/falling/stable from `pending_verifications` history
   - `semantic_search_meals(query, limit)`
2. `ai/graphs/assistant_graph.py` — `create_react_agent(model=ChatGroq(...), tools=[...], checkpointer=...)`.
3. `POST /api/v1/chat` — SSE streaming endpoint. Body: `{ message, lat, lng, thread_id? }`. Stream `thinking` / `tool_call` / `tool_result` / `token` / `done` events.
4. System prompt enforces scope (Islamabad/Rawalpindi food only — refuses off-topic).
5. Frontend: chat panel with live tool-call visibility.

**KPI:** "find biryani under 200 near NUST" → agent calls 2–3 tools → ranked results with explanation, streamed live.

**DoD:**
- Off-topic query ("capital of France") → agent declines, stays in scope
- Follow-up turn uses prior context via checkpointer
- Tool calls visible in SSE stream on frontend

---

## SPRINT 4 — Personalized Feed

**Status:** ⬜

**Tasks:**
1. `ai/chains/personalization_chain.py` — build user taste embedding (centroid of saved-meal embeddings).
2. `pgvector_personalized_search` — blend `0.6 × foodly_score + 0.4 × (1 - taste_distance)`.
3. `GET /api/v1/feed?lat=&lng=&radius_km=` — authenticated → personalized; anonymous → Foodly Score sort.
4. Add `personalization_score` to feed items.

**KPI:** User with saved biryani/desi meals gets a feed skewed toward those categories vs. generic `/nearby`.

**DoD:** Anonymous fallback works; `personalization_score` present and 0–100.

---

## SPRINT 5 — Nightly Enrichment Supervisor (Multi-Agent)

**Status:** ⬜

**Tasks:**
1. `ai/graphs/supervisor_graph.py` — `SupervisorState`, `distribute_node` (fan-out via `Send()`), `aggregate_node`.
2. Wire: top-50 meals by report count → parallel `price_agent` sub-runs → batch insert to `pending_verifications`.
3. APScheduler cron (2am PKT) + `POST /admin/agent/run-enrichment` manual trigger.
4. `GET /admin/agent/enrichment-status`.

**KPI:** 50 parallel sub-agent runs complete within 60s; HTTP server p95 unaffected during the run.

**DoD:** Status endpoint shows `{ completed, failed, in_progress }`; concurrent k6 test shows no HTTP degradation during a run.

---

## SPRINT 6 — LangSmith Observability

**Status:** ⬜

**Tasks:**
1. Wire `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` into config (as a **may-gracefully-degrade** key per the earlier secrets audit — missing key should disable tracing, not crash startup).
2. Tag every chain/graph invocation with `{ meal_id, user_id, endpoint }` metadata.
3. Build eval datasets: `insight_eval_set` (20 meals, ground-truth verdicts), `search_eval_set` (15 queries, expected top-3).
4. Run evaluators, document scores in `docs/ai_eval.md`.
5. Log token cost (`prompt_tokens`, `completion_tokens`, `cost_usd`) per AI endpoint.

**KPI:** Every AI call traced; `insight_eval_set` verdict accuracy ≥ 75%.

**DoD:** LangSmith dashboard shows traces for all 5 chain/graph types with `meal_id`/`user_id` metadata.

---

## SPRINT 7 — AI Streaming Responses

**Status:** ⬜ (price-scraper SSE exists; insight streaming and unified event schema do not)

**Tasks:**
1. `GET /meals/{id}/insight/stream` — SSE token streaming from `insight_chain.astream()`.
2. Align event schema across `insight/stream`, `live-price`, `/chat`: `thinking` / `tool_call` / `tool_result` / `token` / `done`.
3. Frontend `hooks/useSSE.ts` — progressive rendering.
4. Cache only the final assembled insight, never intermediate chunks.

**KPI:** Time-to-first-token < 300ms on insight stream.

**DoD:** Disconnecting mid-stream stops the generator (`request.is_disconnected()` checked).

---

## SPRINT 8 — AI Error Handling & Fallback Audit

**Status:** ⬜ — partial fallback exists in `meal_service.py` (RAG → legacy → error), but no unified wrapper or circuit breaker.

**Tasks:**
1. Audit every AI call path — document failure mode + fallback (table format, per original plan Day 19).
2. Implement `ai/core/safe_invoke.py` — timeout + exception wrapper with defined fallback per call site.
3. Replace ad-hoc `try/except` around chain calls with `safe_invoke(...)`.
4. Circuit breaker for Gemini: 5 consecutive failures → skip for 60s.

**KPI:** Zero 500s from AI failures; all degrade to a defined fallback response.

**DoD:** Setting `GOOGLE_API_KEY`/`GROQ_API_KEY` to garbage values → every affected endpoint returns its fallback, not a 500.

---

## SPRINT 9 — AI Layer Checkpoint (Tests + Zero Fake Data)

**Status:** ⬜

**Tasks:**
1. `tests/ai/` — one test per chain/graph (insight, price agent, assistant, expansion, validator, HITL).
2. Run LangSmith eval targets: insight accuracy ≥ 75%, search recall@5 ≥ 80%.
3. Final fake-data grep sweep: `grep -r "random.uniform\|random.randint\|mock\|fake" backend/app/` → 0 matches.
4. `docs/ai_architecture.md` — one diagram per AI workflow.

**KPI:** All AI workflows tested and passing eval thresholds.

**DoD:** `pytest tests/ai/` — 0 failures.

---

## SPRINT 10 — Query Optimization + Indexing

**Status:** ⬜

**Tasks:**
1. `EXPLAIN (ANALYZE, BUFFERS)` on `/nearby`, `/search`, `/feed`, `/admin/reports`, saved-meals query.
2. Add missing indexes: `meals(restaurant_id)`, `meals(category, price)` *(revisit — no `category` column currently; index on existing columns instead, e.g. `meals(location, price)`)*, `pending_verifications(meal_id, status)`, `saved_meals(user_id)`.
3. Move Foodly Score sort into SQL, not Python loops.
4. Enforce `LIMIT` on every repository method — no unbounded queries.
5. **Also resolve here:** the shared-`Session`-across-threads issue flagged in the RAG insight chain fix — give each parallel retrieval helper its own short-lived `SessionLocal()`.

**KPI:** Zero sequential scans on tables > 100 rows; `/nearby` p95 < 200ms uncached.

**DoD:** `EXPLAIN ANALYZE` shows index scans, not seq scans, on all audited queries.

---

## SPRINT 11 — Redis Caching Layer

**Status:** 🔶 — `core/cache.py` already exists and is used by the insight chain; broader hot-path caching (search, nearby, feed) is not yet wired.

**Tasks:**
1. Extend caching to `/search` (15 min TTL), `/nearby` (5 min TTL), `/feed` (10 min TTL).
2. Cache invalidation on writes — price change invalidates `insight:{meal_id}`, `nearby:*`, `feed:*`.
3. `X-Cache: HIT|MISS` header on all cached responses.
4. Redis health check in `GET /health`.

**KPI:** Cache hit rate > 60% on search; cached latency < 50ms.

**DoD:** Two identical `/search?q=biryani` calls → first `MISS`, second `HIT`.

---

## SPRINT 12 — AI Response Caching Strategy

**Status:** 🔶 — insight caching by `meal_id`+price exists; semantic chat cache and expansion/validation caching do not.

**Tasks:**
1. Semantic cache for `/chat` — embed query, Redis+pgvector cosine-distance lookup (< 0.1 → cache hit).
2. Cache `expansion_chain` results (1 hr TTL), `validation_chain` results (6 hr TTL).
3. Log token savings before/after semantic cache.

**KPI:** ≥ 50% token cost reduction on repeated queries; insight cache hit rate ≥ 80%.

**DoD:** Same chat question asked twice → second call bypasses Groq entirely.

---

## SPRINT 13 — Layer 3 Benchmark + Test Suite Cleanup

**Status:** ⬜

**Tasks:**
1. `k6` load test: 50 VUs × 60s on `/nearby`, `/search`, `/feed`, 5 VUs on `/chat`.
2. Redis hit-rate check (`redis-cli INFO stats`).
3. OWASP ZAP baseline scan — fix HIGH findings.
4. Full `pytest` pass; remove remaining `print()` in `backend/app/` (migrate to `structlog`, extending Sprint 2's start); dead code/import cleanup.
5. `.env.example` fully documents every config var.

**KPI:** All p95 targets met; zero HIGH ZAP findings; 100% pytest pass.

**DoD:** `/nearby` p95 < 150ms cached, < 250ms miss; `grep -r "print(" backend/app/` → 0.

---

## SPRINT 14 — WebSocket Server + Connection Manager

**Status:** ⬜

**Tasks:**
1. `core/websocket_manager.py` — `ConnectionManager` (per-user connection list, send/broadcast/admin-broadcast).
2. `ws://.../api/v1/ws?token=JWT` — auth on connect, close `4001` on invalid token.
3. Heartbeat (30s ping, 10s pong timeout).
4. `hooks/useWebSocket.ts` — exponential backoff reconnect (1s → 30s cap).
5. Redis online-user counter.

**KPI:** Authenticated WS connections stable; auto-reconnect working.

**DoD:** Invalid JWT closes immediately; disconnected tab removed from manager within 5s.

---

## SPRINT 15 — Live Price/Report Notifications

**Status:** ⬜

**Tasks:**
1. Report approve/reject → WS push to reporter.
2. Price change → WS push to all users who saved that meal.
3. New report / HITL pause → WS push to admin connections.
4. Frontend toasts + admin live feed.

**KPI:** Notification round-trip < 200ms, no page refresh.

**DoD:** Approve report → reporter toast appears without polling.

---

## SPRINT 16 — AI Agent Events via WebSocket

**Status:** ⬜

**Tasks:**
1. Move `/chat` from SSE to WS message type `chat_message` (thinking/tool_call/token/done).
2. Price agent job status via WS (`agent_started/searching/found/done`).
3. Frontend chat panel switches SSE → WS.

**KPI:** Single multiplexed WS connection handles chat + notifications + agent events.

**DoD:** Tool-call badges render live; no SSE fallback needed for chat.

---

## SPRINT 17 — Search Suggestions, Presence, WS Load Test

**Status:** ⬜

**Tasks:**
1. Debounced (300ms) `search_suggest` WS message → embed → top-5 suggestions, Redis-cached.
2. Online user count in admin stats, broadcast every 10s.
3. k6 WS load test: 200 connections × 60s.
4. Reconnection test: kill server → verify all clients reconnect within 30s.

**KPI:** Suggestions < 400ms; 200 stable connections with zero dropped messages.

**DoD:** `pytest tests/integration/test_websocket.py` passes.

---

## SPRINT 18 — Kafka Setup + Topics

**Status:** ⬜

**Tasks:**
1. Add `zookeeper` + `kafka` + `kafka-ui` to `docker-compose.yml`.
2. Topics: `report.approved`, `report.rejected`, `meal.price_changed`, `scrape.job_requested`, `scrape.job_completed`, `agent.hitl_decision`.
3. `core/kafka_producer.py` — `emit(topic, key, value)`.
4. Kafka health check in `/health`.

**KPI:** 100-message round-trip, 0 loss, correct order.

**DoD:** Topics visible in kafka-ui; health check reports `kafka: connected`.

---

## SPRINT 19 — Decouple HTTP Handlers via Events

**Status:** ⬜

**Tasks:**
1. `ReportService.approve/reject()` — emit events instead of inline side effects.
2. Price change / agent trigger / HITL decision → corresponding events.
3. Measure before/after response time.

**KPI:** Report approval HTTP response < 50ms.

**DoD:** No WS calls, cache invalidation, or email sends left inside HTTP handlers.

---

## SPRINT 20 — Event Consumers (Workers)

**Status:** ⬜

**Tasks:**
1. `workers/notification_worker.py`, `workers/cache_worker.py`, `workers/email_worker.py`.
2. Each as its own `docker-compose.yml` service.
3. Consumer lag alerting (> 100 messages → warning log).

**KPI:** Approve report → WS notification + cache invalidation + email, all within 2s.

**DoD:** Stopping/restarting a worker → queued events still processed (Kafka durability verified).

---

## SPRINT 21 — AI Agent Pipeline via Kafka

**Status:** ⬜

**Tasks:**
1. `workers/scraper_worker.py`, `workers/verification_worker.py`, `workers/hitl_worker.py`.
2. APScheduler cron emits 50 `scrape.job_requested` events nightly.
3. Confirm HTTP p95 unaffected during scraping run.

**KPI:** 50 events processed, results in `pending_verifications`, HITL resume works via worker.

**DoD:** Concurrent k6 test shows no HTTP degradation during nightly run.

---

## SPRINT 22 — Correlation IDs, DLQ, Layer 5 Checkpoint

**Status:** ⬜

**Tasks:**
1. `correlation_id: uuid4()` on every event; logged by every consumer.
2. DLQ (`{topic}.dlq`) after 3 consumer failures + alert.
3. `tests/integration/test_event_pipeline.py`.
4. `docs/event_topology.md`.
5. Full end-to-end smoke test: chat → save → report → AI validate → HITL approve → Kafka event → WS notification.

**KPI:** Every event traceable; DLQ works; full stack integration test passes.

**DoD:** All consumer lags < 10 in steady state.

---

## SPRINT 23 — Post-Event Perf Audit + Docker Compose (Full Stack)

**Status:** ⬜

**Tasks:**
1. k6 load test with all workers running (100 VUs × 120s) — confirm no HTTP regression vs. Layer 3 benchmarks.
2. `backend/Dockerfile` (multi-stage, target < 200MB), `frontend/Dockerfile` (3-stage).
3. Full `docker-compose.yml` (all services) + `.override.yml` (dev) + `.prod.yml` (prod).

**KPI:** `docker-compose up --build` → all services healthy within 60s; HTTP p95 unregressed.

**DoD:** Backend image < 200MB; data persists across `down && up`.

---

## SPRINT 24 — CI/CD Pipeline

**Status:** ⬜

**Tasks:**
1. `.github/workflows/ci.yml` — services up, migrations, `pytest --cov`, `ruff`, `mypy`, `eslint`. Fail under 70% coverage.
2. `.github/workflows/deploy.yml` — build → ECR → ECS deploy → migrations, on merge to `main`.
3. Branch protection requiring CI pass.
4. All secrets via GitHub Actions secrets store — never in `.yml`.

**KPI:** Failing PR blocked from merge; main merge → ECR image within 5 min.

**DoD:** `grep` confirms no secrets in any workflow file.

---

## SPRINT 25 — AWS Infrastructure

**Status:** ⬜

**Tasks:**
1. VPC (public/private subnets), RDS PostgreSQL 15 (PostGIS+pgvector, 7-day backups), ElastiCache Redis.
2. ECS Fargate: backend + worker services.
3. ALB + ACM HTTPS, Route 53.
4. AWS Secrets Manager for all credentials/API keys.

**KPI:** `https://api.foodly.pk/health` → `200` with valid SSL.

**DoD:** No secrets in ECS task definitions — all via Secrets Manager.

---

## SPRINT 26 — Structured Logging/Metrics + Production Load Test

**Status:** ⬜ (builds on Sprint 2/13's partial `structlog` start)

**Tasks:**
1. Complete `structlog` migration across the entire backend.
2. `prometheus-fastapi-instrumentator` metrics; CloudWatch dashboards.
3. Alerts: p95 > 500ms, error rate > 1%, RDS CPU > 80%.
4. Sentry integration.
5. k6 production load test (200 VUs), DB pool tuning.

**KPI:** 200 concurrent users at p95 < 200ms; AI endpoints stable under load.

**DoD:** Sentry captures a forced 500 within 30s; alert fires on injected error-rate spike.

---

## SPRINT 27 — Security Audit + AI Cost Optimization

**Status:** 🔶 — much of the OWASP groundwork (auth, CORS, secrets, rate limiting) is done by this point; this sprint is verification + the remaining audit items.

**Tasks:**
1. OWASP ZAP active scan against staging — fix HIGH/CRITICAL.
2. `pip-audit` + `npm audit`; `truffleHog` for leaked secrets in git history.
3. LangSmith PII check — `hide_inputs=True` on sensitive chains.
4. Token budgets per chain (insight ≤ 2000 tokens, chat ≤ 500/turn, expansion ≤ 100, validator ≤ 200).
5. Model routing confirmation (Groq for fast/cheap, Gemini for insight reasoning).
6. `docs/cost_model.md` — projected monthly AI cost at 1,000 MAU.

**KPI:** 0 HIGH/CRITICAL ZAP findings; projected cost ≤ $50/month at 1,000 MAU.

**DoD:** `truffleHog` clean; token budgets enforced in code, not just documented.

---

## SPRINT 28 — Final Integration Test + Demo Flow

**Status:** ⬜

**Tasks:**
1. Full production smoke test: register → login → search → chat → feed → save → report → AI validate → admin HITL approve → WS notify → insight loads → bookmark.
2. 100% `pytest` pass.
3. Verify every KPI in the summary table below.
4. Record 3-minute demo video.
5. `ARCHITECTURE.md` with full system + AI workflow diagrams.

**KPI:** End-to-end smoke test passes with zero manual intervention.

**DoD:** All KPIs in the summary table are green.

---

## SPRINT 29 — Analytics + Monetization

**Status:** ⬜

**Tasks:**
1. Analytics (Vercel Analytics + Mixpanel): searches, meal views, saves, reports, chat sessions.
2. Admin analytics dashboard: top searches/meals, report conversion funnel.
3. `is_featured` flag + admin toggle endpoint.
4. Premium plan stub (`users.plan`), price alert system (Resend email on price drop).

**KPI:** Funnel tracked end-to-end; featured listings live; price alerts fire correctly.

**DoD:** Price drop below a saved alert threshold → email sent.

---

## SPRINT 30 — Viral Features, A/B Testing, Investor Metrics, Final Polish

**Status:** ⬜

**Tasks:**
1. Shareable OG meal cards; reporter leaderboard; "Meal of the Day."
2. AI-generated meal descriptions for empty-description meals (cheap Groq chain, nightly cron).
3. A/B test: vector-only vs. vector+expansion search (GrowthBook).
4. Feedback widget + NPS survey.
5. `/admin/investor-metrics` dashboard (MAU/DAU, AI usage stats, revenue) with PDF export.
6. Final UX polish, `README.md` architecture overview, data room prep, demo rehearsal, 90-day retrospective.

**KPI:** Investor-ready dashboard live; demo rehearsed; all documentation committed.

**DoD:** PDF export works; retrospective document committed alongside final `README.md`.

---

## 30-Sprint KPI Summary

| KPI | Sprint 9 (AI checkpoint) | Sprint 22 (Event checkpoint) | Sprint 30 (Final) |
|-----|--------------------------|-------------------------------|--------------------|
| Meals in DB (real data) | ≥ 200 | ≥ 200 | ≥ 500 |
| Fake data instances | 0 | 0 | 0 |
| LangGraph agents live | 3 (price + HITL + assistant) | 4 (+supervisor) | 4 |
| LangChain chains live | 5 (insight, expansion, validator, personalization, description*) | 5 | 6 |
| Insight verdict accuracy | ≥ 75% | ≥ 75% | ≥ 80% |
| Search recall@5 | ≥ 80% | ≥ 80% | ≥ 85% |
| `/nearby` p95 (cached) | — | — | < 150ms |
| `/insight` / `/chat` time-to-first-token | < 300ms | < 300ms | < 300ms |
| WS notification latency | — | < 200ms | < 200ms |
| API error rate @ 200 VUs | — | — | < 1% |
| Token cost projected @ 1K MAU | — | — | ≤ $50/month |
| OWASP ZAP HIGH findings | 0 | 0 | 0 |
| pytest pass rate | 100% | 100% | 100% |
| Kafka consumer lag (steady state) | — | < 10 | < 10 |

*description chain lands in Sprint 30, not Sprint 9 — table reflects target cumulative state, not per-sprint order.

---

## What Changed From v5.0 (Day-Based Plan)

1. **60 days → 30 sprints**, sized by actual remaining effort rather than fixed calendar days.
2. **Layer 1 and part of Layer 2/OWASP hardening are already done** — reflected as Sprint 1 (verification) and Sprint 2 (finishing touches) rather than full from-scratch builds.
3. **Two bugs discovered during implementation are now explicit line items**, not just footnotes: the RAG insight chain's shared-`Session`-across-threads issue (→ Sprint 10) and the `Meal.category` schema decision (already resolved by relying on `pgvector` similarity + `location`/`confidence`, documented at the time of the fix).
4. **AI provider keys reclassified**: LangSmith/third-party AI keys are "may-gracefully-degrade" config (missing → feature disables, not app crash), distinct from `SECRET_KEY`/`DATABASE_URL` which are "must-fail-startup" secrets — this distinction was flagged as a follow-up in the secrets-hardening work and is now scheduled into Sprint 6.
5. **Growth/investor-prep phase (old Layer 7, 14 days) compressed into 2 sprints** — reasonable since analytics/monetization/viral features are lower technical risk than the AI/event/production layers and don't need day-by-day granularity.

---

*Version 6.0 · July 2026 · Next review: Sprint 9 (AI layer checkpoint)*