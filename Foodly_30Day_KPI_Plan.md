# Foodly — 30-Day KPI Plan (4 Hours/Day)
**Starting:** July 1, 2026  
**Daily Commitment:** 4 hours  
**Target:** Investor-ready MVP with working AI features  
**Total Hours:** 120 hours (30 days × 4 hrs)

---

## 📊 ACTUAL CODEBASE STATE (July 1, 2026)

### ✅ What's Actually Built & Working

| Component | Status | Evidence |
|-----------|--------|----------|
| **FastAPI Backend** | ✅ Solid | `main.py` with all routers, CORS, health check |
| **PostgreSQL + PostGIS + pgvector** | ✅ Working | 5 tables, spatial indexes, vector indexes |
| **Service Layer + Repository Pattern** | ✅ Implemented | `MealService`, `MealRepository` properly decoupled |
| **Query Expansion (LangChain)** | ✅ Built & Integrated | `query_expansion_chain.py` used in `meal.py:150-152` |
| **Report Validator (LangChain)** | ✅ Working | `validation_chain.py` with Groq structured output |
| **LangGraph Price Scraper** | ✅ Working | Retry logic functional (`should_continue` returns "retry"/"store"/"end") |
| **RAG-Grounded AI Insight** | ✅ Built | `insight_chain.py` with pgvector similarity, sector stats, price history |
| **Redis Caching** | ⚠️ Partial | `core/cache.py` exists, used for search + insight, NO invalidation |
| **Embeddings Service** | ✅ Working | Gemini `text-embedding-004` async integration |
| **Frontend (Next.js 16)** | ✅ 80% Complete | Homepage, map, meal cards, admin dashboard, report form |
| **JWT Authentication** | ✅ Working | Register, login, `/me` endpoint with bcrypt |
| **Community Reports + Admin** | ✅ Working | Submit, approve/reject, confidence system |

### ❌ What's Actually Missing (Critical)

| Gap | Severity | Impact |
|-----|----------|--------|
| **NO tests** | 🔴 BLOCKER | Zero verification, unprofessional for investors |
| **NO rate limiting** | 🔴 BLOCKER | API vulnerable to abuse, AI costs uncontrolled |
| **NO Docker Compose** | 🔴 BLOCKER | Can't deploy, environment inconsistency |
| **NO CI/CD** | 🟡 HIGH | Manual deployment, no quality gates |
| **NO LangSmith** | 🟡 HIGH | Zero observability, can't measure AI quality |
| **NO HITL checkpointer** | 🟡 HIGH | Agent state lost on restart |
| **CORS allows all origins** | 🟡 HIGH | Security vulnerability |
| **NO security headers** | 🟡 MEDIUM | Missing X-Content-Type-Options, etc. |
| **ThreadPoolExecutor in AI** | 🟡 MEDIUM | Blocks event loop (insight_chain.py:447-472) |
| **NO structured logging** | 🟢 LOW | Hard to debug production issues |

---

## 🎯 30-DAY REALISTIC TIMELINE

### Design Philosophy (4 hrs/day):
1. **Investor demo first** — Working features > perfect code
2. **Quality gates** — Tests and security before new features
3. **No over-engineering** — Skip Kafka, WebSockets, complex multi-agent
4. **Ship fast, iterate later** — Get to deployable MVP in 30 days

---

## PHASE 1: FIX CRITICAL BUGS & SECURITY (Days 1-7)

### Day 1 — July 1: Redis Cache Invalidation + Monitoring
**🎯 KPI:** Cache invalidation working. Cache hit rate measurable.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Add `invalidate_pattern()` to `core/cache.py` — delete keys by pattern | `backend/app/core/cache.py` |
| 30m | Add cache invalidation hooks in admin approve/reject endpoints | `backend/app/api/endpoints/admin.py`, `reports.py` |
| 30m | Add `X-Cache: HIT | MISS` header middleware | `backend/app/core/cache.py` |
| 30m | Add cache hit counter (Redis INCR) — `cache_hits:{endpoint}` | `backend/app/core/cache.py` |
| 1h | Add price-aware cache key: `insight:{meal_id}:{price_cents}` | `backend/app/services/meal.py` |
| 1h | Write cache validation script — `scripts/validate_cache.py` | New file |

**✅ DoD:** Two identical nearby API calls → first MISS, second HIT. Price change invalidates insight cache.

---

### Day 2 — July 2: Security Hardening
**🎯 KPI:** CORS restricted, security headers added, SQL injection prevented.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Restrict CORS to frontend origin (not `*`) | `backend/app/main.py:16` |
| 30m | Add security headers middleware (5 headers) | New: `backend/app/core/security_headers.py` |
| 30m | Add JWT auth to reports endpoint (optional but track reporter) | `backend/app/api/endpoints/reports.py` |
| 1h | Add input sanitization — `bleach.clean()` on string inputs | `reports.py`, `meals.py` |
| 1h | SQL injection test: `'; DROP TABLE meals; --` in search → safe | Manual test |
| 30m | Migrate admin auth from shared secret to role-based JWT | `backend/app/api/endpoints/admin.py` |

**✅ DoD:** CORS restricted to `http://localhost:3000`. Security headers on all responses. SQL injection returns empty results, not 500.

---

### Day 3 — July 3: Rate Limiting
**🎯 KPI:** API protected with rate limits.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Install `slowapi`, configure rate limits per endpoint | `backend/app/main.py` |
| 1h | Rate limits: global 100/min, login 5/min, search 30/min, reports 10/min | `backend/app/core/config.py` |
| 1h | Add `429 Retry-After` header on rate limit responses | Middleware |
| 1h | Test: 6th login attempt in 1 min → 429 | Manual test |

**✅ DoD:** 6th login attempt in 1 minute → 429 with Retry-After header.

---

## PHASE 2: QUALITY & TESTING (Days 4-10)

### Day 4 — July 4: Test Infrastructure
**🎯 KPI:** `pytest` suite with 10+ passing tests.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Set up pytest config, `conftest.py` with test DB fixture | New: `backend/tests/conftest.py` |
| 1h | Auth tests: register, login, wrong password → 401, expired token → 401 | `tests/test_auth.py` |
| 1h | Meals tests: list, nearby, search, create (admin only → 403) | `tests/test_meals.py` |
| 1h | Reports tests: submit, approve, reject, duplicate constraint | `tests/test_reports.py` |
| 30m | AI tests: insight chain returns valid verdict, validator rejects spam | `tests/test_ai.py` |

**✅ DoD:** `pytest tests/` — 10+ tests, 0 failures.

---

### Day 5 — July 5: More Tests + Coverage
**🎯 KPI:** 20+ passing tests. Coverage > 40%.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Admin tests: stats, report list, bulk approve, approve/reject | `tests/test_admin.py` |
| 1h | Cache tests: set/get, invalidation, TTL expiry | `tests/test_cache.py` |
| 1h | Integration test: full flow — register → search → save → report → admin approve | `tests/test_integration.py` |
| 1h | Run coverage, document gaps, add tests for uncovered code | Terminal |

**✅ DoD:** `pytest tests/ --cov=app --cov-report=html` — 20+ tests, coverage > 40%.

---

### Day 6 — July 6: AI Safe Invoke + Fallbacks
**🎯 KPI:** AI calls wrapped with fallbacks. Zero 500 errors on AI failures.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Build `safe_invoke(chain, input, fallback, timeout_s=10)` | New: `backend/ai/core/safe_invoke.py` |
| 1h | Replace raw `chain.ainvoke()` with `safe_invoke()` — insight, expansion, validator | All chain files |
| 1h | Add circuit breaker: 5 consecutive failures → skip AI for 60s | `backend/ai/core/circuit_breaker.py` |
| 1h | Test fallbacks: set wrong API keys → verify degraded responses | Manual test |

**✅ DoD:** Set `GOOGLE_API_KEY=wrong` → all AI calls return fallback, zero 500 errors.

---

### Day 7 — July 7: Remove ThreadPoolExecutor
**🎯 KPI:** All AI calls async. No blocking event loop.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Replace `ThreadPoolExecutor` in `insight_chain.py:447-472` with `asyncio.gather()` | `backend/ai/chains/insight_chain.py` |
| 1h | Audit all AI calls for sync/async issues | All `backend/ai/` files |
| 1h | Add timeout to all AI calls (10s for insight, 5s for expansion/validator) | All chain files |
| 1h | Load test: 10 concurrent AI calls → no blocking, all complete | Manual test |

**✅ DoD:** 10 concurrent `/meals/1` requests → all complete in < 15s, no event loop blocking.

---

## PHASE 3: INFRASTRUCTURE & DEPLOYMENT (Days 8-14)

### Day 8 — July 8: Docker Compose
**🎯 KPI:** `docker-compose up --build` → all services healthy.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Create `backend/Dockerfile` — multi-stage, target < 200MB | New: `backend/Dockerfile` |
| 1h | Create `frontend/Dockerfile` — 3-stage Next.js standalone | New: `frontend/Dockerfile` |
| 1h | Update `docker-compose.yml` — add postgres, backend, frontend, redis | `docker-compose.yml` |
| 1h | Add health checks, wait-for-it dependencies, env vars | `docker-compose.yml` |

**✅ DoD:** `docker-compose up --build` → all services healthy within 60s. `localhost:8000/health` returns 200.

---

### Day 9 — July 9: GitHub Actions CI
**🎯 KPI:** PR with failing test → CI fails → merge blocked.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Create `.github/workflows/ci.yml` — pytest, ruff, eslint on PR | New: `.github/workflows/ci.yml` |
| 1h | Create `.github/workflows/deploy.yml` — build image, push to registry | New: `.github/workflows/deploy.yml` |
| 1h | Set up GitHub secrets: DATABASE_URL, API keys, Docker registry | GitHub settings |
| 30m | Test CI: push branch with failing test → verify CI fails | GitHub |
| 30m | Add badge to README.md | `README.md` |

**✅ DoD:** PR with failing test → CI fails → merge blocked. Merge to main → image built.

---

### Day 10 — July 10: Cloud Deployment
**🎯 KPI:** API deployed to cloud. HTTPS working. Health check passes.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Deploy backend to Railway/Render (free tier) | Cloud dashboard |
| 1h | Deploy frontend to Vercel (free tier) — connect GitHub repo | Vercel dashboard |
| 1h | Set up custom domain + HTTPS (or use default *.vercel.app) | DNS + SSL |
| 30m | Set up all environment variables in cloud dashboard | Cloud dashboard |
| 30m | Test: `GET /health` → `{ "status": "ok", "database": "connected" }` | curl test |

**✅ DoD:** `https://foodly-backend.onrender.com/health` returns 200. Frontend loads at `https://foodly.vercel.app`.

---

## PHASE 4: OBSERVABILITY & PERFORMANCE (Days 11-14)

### Day 11 — July 11: Structured Logging + Sentry
**🎯 KPI:** Structured JSON logs. Error tracking live.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Set up `structlog` — JSON logs with timestamp, level, endpoint, latency | New: `backend/app/core/logging.py` |
| 1h | Add `prometheus-fastapi-instrumentator` — HTTP metrics | `backend/app/main.py` |
| 1h | Set up Sentry for error tracking — `sentry-sdk` with 10% sample rate | `backend/app/main.py` |
| 1h | Test: trigger 500 error → Sentry shows stack trace within 30s | Manual test |

**✅ DoD:** Trigger intentional 500 → Sentry captures it. Logs are structured JSON in Render logs.

---

### Day 12 — July 12: LangSmith Integration
**🎯 KPI:** All AI calls traced in LangSmith. First eval dataset.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Add LangSmith env vars to `core/config.py` | `backend/app/core/config.py` |
| 30m | Tag all chains with metadata (meal_id, endpoint, user_id) | All chain files |
| 1h | Create insight eval set — 10 meals with expected verdicts | LangSmith dashboard |
| 1h | Create search eval set — 10 queries with expected top-3 meals | LangSmith dashboard |
| 1h | Run evaluations, document scores in `docs/ai_eval.md` | New file |

**✅ DoD:** LangSmith shows traces for insight_chain, expansion_chain, validation_chain. Insight verdict_accuracy documented.

---

### Day 13 — July 13: Performance Baselines
**🎯 KPI:** p95 latency documented. Cache hit rate > 60%.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Install k6, write `load_test.js` — test `/meals`, `/nearby`, `/search` | New: `load_test.js` |
| 1h | Run k6: 20 VUs × 60s. Record p50, p95, p99, req/s, error rate | Terminal |
| 1h | Separate AI test: 5 VUs × 60s on `/meals/{id}` (insight) | Terminal |
| 1h | Document results in `docs/benchmarks.md` | New file |

**✅ DoD:** `/nearby` p95 < 200ms (cached). `/insight` time-to-first-token < 300ms. Error rate < 1%.

---

### Day 14 — July 14: Investor Demo Prep
**🎯 KPI:** Full demo flow working end-to-end. README updated.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Stitch demo flow: register → search "biryani F-7" → get RAG insight → save meal → submit report → admin approves | All systems |
| 1h | Record 2-minute screen demo (no voiceover) | Screen recorder |
| 1h | Update `README.md` with architecture, local setup, AI features, deploy URL | `README.md` |
| 1h | Prepare data room: architecture diagram, benchmarks, AI eval scores | `docs/investor/` folder |
| 30m | Rehearse demo — ensure < 2 mins, zero errors | Dry run |

**✅ DoD:** Full demo flow works on production. README updated with live URLs. Data room ready.

---

## PHASE 5: POLISH & MONETIZATION (Days 15-30)

### Days 15-17: Basic Monetization Features
**Days:** July 15-17  
**Goal:** Add revenue features for investor pitch.

#### Day 15 — July 15: Featured Listings
**🎯 KPI:** Admin can mark meals as featured. Featured meals show badge.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add `is_featured` column to meals table (already exists in schema) | Migration |
| 1h | Add featured toggle in admin dashboard | `frontend/src/app/admin/page.tsx` |
| 1h | Show featured badge on meal cards in homepage | `frontend/src/app/page.tsx` |
| 1h | Add "Featured" filter in search | `backend/app/api/endpoints/meals.py` + frontend |

**✅ DoD:** Admin toggles featured → badge appears on meal card within 5 minutes.

---

#### Day 16 — July 16: Reporter Leaderboard
**🎯 KPI:** Leaderboard shows top 10 reporters by approved reports.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Create `GET /api/v1/reports/leaderboard` endpoint | `backend/app/api/endpoints/reports.py` |
| 1h | Build leaderboard UI in admin dashboard | `frontend/src/app/admin/page.tsx` |
| 1h | Add karma score display on user profile | `frontend/src/app/meals/[id]/page.tsx` |
| 1h | Test: submit 5 reports → appear on leaderboard | Manual |

**✅ DoD:** Top 10 reporters displayed with name, approved reports count, karma score.

---

#### Day 17 — July 17: Price Alerts (Email)
**🎯 KPI:** Users can subscribe to price drop alerts.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add `price_alerts` table (user_id, meal_id, threshold_price, active) | Migration |
| 1h | Create `POST /api/v1/meals/{id}/alert` endpoint | `backend/app/api/endpoints/meals.py` |
| 1h | Build alert form in meal detail page | `frontend/src/app/meals/[id]/page.tsx` |
| 1h | Add Resend integration for email alerts (when price drops) | New: `backend/app/services/email.py` |

**✅ DoD:** User sets alert for PKR 300 → meal drops to PKR 280 → email sent within 24h.

---

### Days 18-21: Analytics & Metrics
**Days:** July 18-21  
**Goal:** Track user behavior and investor metrics.

#### Day 18 — July 18: Basic Analytics
**🎯 KPI:** Track search queries, meal views, saves, reports.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add `analytics_events` table (event_type, user_id, meal_id, metadata, timestamp) | Migration |
| 1h | Create `POST /api/v1/analytics/event` endpoint | New endpoint |
| 1h | Emit events from frontend: search, view, save, report | Frontend components |
| 1h | Build analytics dashboard in admin panel | `frontend/src/app/admin/page.tsx` |

**✅ DoD:** Admin dashboard shows: total searches, top searches, meal views, saves, reports (last 7 days).

---

#### Day 19 — July 19: Investor Metrics Dashboard
**🎯 KPI:** Real-time KPIs for investor pitch.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Create `GET /api/v1/admin/investor-metrics` endpoint | `backend/app/api/endpoints/admin.py` |
| 1h | Calculate metrics: MAU, DAU, avg session time, conversion funnel | Backend |
| 1h | Build investor metrics UI (big numbers, charts) | `frontend/src/app/admin/page.tsx` |
| 1h | Add export to PDF functionality | `backend/app/services/pdf.py` |

**✅ DoD:** `/admin/investor-metrics` shows: total users, active users, meals indexed, reports submitted, AI accuracy.

---

#### Day 20 — July 20: Mixpanel Analytics
**🎯 KPI:** User behavior tracked in Mixpanel.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Install Mixpanel SDK, set up project | `frontend/package.json` |
| 1h | Track events: signup, login, search, view_meal, save_meal, submit_report | Frontend |
| 1h | Build Mixpanel dashboard: retention, funnels, user paths | Mixpanel dashboard |
| 1h | Set up Mixpanel alerts for key metrics (signups, reports) | Mixpanel |

**✅ DoD:** Mixpanel shows: signup funnel, search → view → save conversion, daily active users.

---

#### Day 21 — July 21: Feedback Widget + NPS
**🎯 KPI:** Collect user feedback. NPS score calculated.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add feedback form (Tally embed or custom) after 5th session | Frontend |
| 1h | Create `POST /api/v1/feedback` endpoint | New endpoint |
| 1h | Send NPS survey email to all registered users (Resend) | `backend/app/services/email.py` |
| 1h | Build NPS dashboard in admin panel | `frontend/src/app/admin/page.tsx` |

**✅ DoD:** 50+ feedback responses collected. NPS score displayed in admin panel.

---

### Days 22-25: Performance & Polish
**Days:** July 22-25  
**Goal:** Optimize performance, fix UX issues.

#### Day 22 — July 22: Cache Optimization
**🎯 KPI:** Cache hit rate > 60%. Token costs reduced 40%.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add cache hit rate logging per endpoint | `backend/app/core/cache.py` |
| 1h | Optimize TTLs: insight 48h, search 10min, nearby 5min | `backend/app/services/meal.py` |
| 1h | Add cache warming on meal create/update — pre-compute insight | `backend/app/services/meal.py` |
| 1h | Measure token cost before/after using LangSmith | LangSmith dashboard |

**✅ DoD:** Cache hit rate > 60% on search and insight. Token cost per 100 insight calls reduced 40%.

---

#### Day 23 — July 23: UX Improvements
**🎯 KPI:** Fix top 5 UX issues from dogfooding.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add loading skeletons for meal cards | Frontend |
| 1h | Add error boundaries + user-friendly error messages | Frontend |
| 1h | Optimize images — lazy loading, WebP format | Frontend |
| 1h | Add "Back to top" button, smooth scroll | Frontend |

**✅ DoD:** PageSpeed score > 80. No layout shifts. Images load in < 1s.

---

#### Day 24 — July 24: SEO + Meta Tags
**🎯 KPI:** Proper SEO for all pages.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add meta tags (title, description, OG) to all pages | Frontend |
| 1h | Add sitemap.xml + robots.txt | `frontend/public/` |
| 1h | Add structured data (JSON-LD) for meals | Frontend |
| 1h | Test with Google Rich Results Test | Manual |

**✅ DoD:** All pages have proper meta tags. Sitemap submitted to Google Search Console.

---

#### Day 25 — July 25: Performance Audit
**🎯 KPI:** Identify and fix slow queries.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Enable SQLAlchemy query logging, identify N+1 queries | Backend |
| 1h | Add database indexes for slow queries | Migration |
| 1h | Optimize vector search — add HNSW index tuning | Migration |
| 1h | Add query result caching for sector stats | `backend/app/services/meal.py` |

**✅ DoD:** All queries < 100ms. No N+1 queries. Vector search < 50ms.

---

### Days 26-30: Final Polish & Investor Prep
**Days:** July 26-30  
**Goal:** Final integration test, demo video, investor meeting prep.

#### Day 26 — July 26: Integration Test Suite
**🎯 KPI:** Full end-to-end test suite passing.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Write 5 end-to-end tests (Playwright or Cypress) | `frontend/tests/e2e/` |
| 1h | Test: register → search → view → save → report → admin approve → price update | E2E test |
| 1h | Test: AI insight generation → verify RAG context in response | E2E test |
| 1h | Run full test suite, fix any failing tests | Terminal |

**✅ DoD:** 5 E2E tests passing. Full test suite (unit + integration + E2E) = 30+ tests, 0 failures.

---

#### Day 27 — July 27: Documentation
**🎯 KPI:** Complete documentation for developers and investors.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Write `docs/ai_architecture.md` — ASCII diagrams for all AI workflows | New file |
| 1h | Write `docs/api_reference.md` — all endpoints with examples | New file |
| 1h | Write `docs/deployment.md` — how to deploy to production | New file |
| 1h | Update `README.md` with badges, screenshots, demo video link | `README.md` |

**✅ DoD:** All docs committed. README has: badges, architecture diagram, API docs link, demo video.

---

#### Day 28 — July 28: Demo Video + Pitch Deck
**🎯 KPI:** Professional demo video and pitch deck.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Record 3-minute demo video (OBS or Loom) | Video |
| 1h | Edit video — add captions, zoom on key features | Video editor |
| 1h | Create pitch deck (10 slides) — problem, solution, traction, team, ask | PDF |
| 1h | Upload video to YouTube (unlisted), add to pitch deck | YouTube |

**✅ DoD:** 3-minute demo video live. Pitch deck PDF ready.

---

#### Day 29 — July 29: Final Bug Bash
**🎯 KPI:** Zero critical bugs. All features working.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Test all critical paths on production | Manual |
| 1h | Fix any bugs found | Various |
| 1h | Test on mobile (responsive design) | Manual |
| 1h | Load test production — 10 VUs × 5 min | k6 |

**✅ DoD:** Zero critical bugs. Production handles 10 concurrent users. Mobile responsive.

---

#### Day 30 — July 30: Investor Meeting Prep
**🎯 KPI:** Ready for investor meetings.  
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Prepare data room: architecture diagram, benchmarks, AI eval scores, test results | `docs/investor/` |
| 1h | Write one-pager: problem, solution, traction, team, market size | PDF |
| 1h | Rehearse 5-minute pitch + 2-minute demo | Dry run |
| 1h | Final checklist: demo works, docs ready, metrics tracked | Checklist |

**✅ DoD:** Data room complete. 5-minute pitch rehearsed. Ready for investor meetings.

---

## 📊 30-DAY CONSENSUS KPIs (July 30, 2026 — Final Target)

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Demos & Investor** |
| Demo flow working end-to-end | ✅ Pass | Manual test |
| Investor metrics dashboard | ✅ Live | `/admin/investor-metrics` |
| Data room (docs + tests + benchmarks) | ✅ Complete | `docs/investor/` folder |
| **AI Features** |
| RAG-grounded insight | ✅ Live | `insight_chain.py` with pgvector |
| Query expansion | ✅ Live | `expansion_chain.py` |
| Report validator | ✅ Live | `validation_chain.py` |
| Price scraper with retry | ✅ Live | `price_scraper.py` |
| LangSmith traces | All AI calls | LangSmith dashboard |
| Insight verdict_accuracy | ≥ 75% | LangSmith eval |
| **Quality** |
| `pytest` pass rate | 100% | 30+ tests, 0 failures |
| Test coverage | > 40% | `pytest --cov` |
| AI error rate | < 0.5% | Sentry + manual testing |
| **Security** |
| Rate limiting | Active | `slowapi` |
| CORS restricted | ✅ Yes | Frontend origin only |
| Security headers | ✅ All 5 | X-Content-Type-Options, etc. |
| **Performance** |
| `/nearby` p95 (cached) | < 200ms | k6 load test |
| `/insight` time-to-first-token | < 300ms | k6 load test |
| Cache hit rate | > 60% | Redis metrics |
| **Infrastructure** |
| Docker Compose up | One command | `docker-compose up` |
| Cloud deployment | HTTPS live | Vercel + Railway/Render |
| CI/CD | Auto-deploy | GitHub Actions |
| **Analytics** |
| Mixpanel tracking | Live | Search, views, saves, reports |
| NPS score | Calculated | Admin panel |
| Reporter leaderboard | Live | Top 10 reporters |

---

## ⚡ THE 80/20 RULE — What Gets You 80% of Investor Value

If you have **only 10 more days**, focus on this:

### Week 1 (Jul 1-7): Fix Foundation
1. **Jul 1** — Redis cache invalidation + monitoring
2. **Jul 2** — Security hardening (CORS, headers, SQL injection)
3. **Jul 3** — Rate limiting
4. **Jul 4-5** — Test suite (20+ tests)
5. **Jul 6** — AI safe invoke + remove ThreadPoolExecutor
6. **Jul 7** — Async AI calls

### Week 2 (Jul 8-14): Ship It
7. **Jul 8** — Docker Compose
8. **Jul 9** — CI/CD (GitHub Actions)
9. **Jul 10** — 🔥 **Deploy to production** (Vercel + Railway)
10. **Jul 11** — Structured logging + Sentry
11. **Jul 12** — LangSmith tracing
12. **Jul 13** — Performance baselines
13. **Jul 14** — 🔥 **Investor demo ready**

**After 14 days (Jul 14), you'll have:**
- ✅ Deployed to cloud with HTTPS
- ✅ Rate-limited, secure API
- ✅ 20+ tests passing
- ✅ LangSmith traces proving AI quality
- ✅ Investor demo ready

**That's enough for investor conversations.**

---

## 🚨 CRITICAL: DON'T BUILD THESE (Yet)

| Feature | Why Skip Now |
|---------|--------------|
| **Kafka** (event-driven) | Overkill for MVP — Redis Pub/Sub is fine at current scale |
| **WebSockets** | SSE works for demos, add WS when you have 100+ concurrent users |
| **Multi-agent supervisor** | Too complex for 4 hrs/day — single agent is enough for demo |
| **Personalized feed** | Requires many users with history — you don't have that yet |
| **A/B testing framework** | Premature optimization — you need users first |
| **OWASP ZAP active scan** | Passive security (headers + rate limits) is enough for demo |
| **Kafka consumers** | No Kafka yet — skip until you need async workers |

---

## 📈 TIME BUDGET TRACKER (4 hours/day)

```
Week 1: Fix Foundation (Jul 1-7)
─────────────────────────────────
 1  Jul  1  Redis cache invalidation       4 hrs     4 hrs
 2  Jul  2  Security hardening             4 hrs     8 hrs
 3  Jul  3  Rate limiting                  4 hrs    12 hrs
 4  Jul  4  Test infrastructure            4 hrs    16 hrs
 5  Jul  5  Test suite (20+ tests)         4 hrs    20 hrs
 6  Jul  6  AI safe invoke + fallbacks     4 hrs    24 hrs
 7  Jul  7  Remove ThreadPoolExecutor      4 hrs    28 hrs

Week 2: Ship It (Jul 8-14)
─────────────────────────────────
 8  Jul  8  Docker Compose                 4 hrs    32 hrs
 9  Jul  9  CI/CD (GitHub Actions)         4 hrs    36 hrs
10  Jul 10  Deploy to cloud                4 hrs    40 hrs
11  Jul 11  Structured logging + Sentry    4 hrs    44 hrs
12  Jul 12  LangSmith integration          4 hrs    48 hrs
13  Jul 13  Performance baselines          4 hrs    52 hrs
14  Jul 14  Investor demo prep             4 hrs    56 hrs

Week 3: Monetization (Jul 15-21)
─────────────────────────────────
15  Jul 15  Featured listings              4 hrs    60 hrs
16  Jul 16  Reporter leaderboard           4 hrs    64 hrs
17  Jul 17  Price alerts (email)           4 hrs    68 hrs
18  Jul 18  Basic analytics                4 hrs    72 hrs
19  Jul 19  Investor metrics dashboard     4 hrs    76 hrs
20  Jul 20  Mixpanel analytics             4 hrs    80 hrs
21  Jul 21  Feedback widget + NPS          4 hrs    84 hrs

Week 4: Polish (Jul 22-30)
─────────────────────────────────
22  Jul 22  Cache optimization             4 hrs    88 hrs
23  Jul 23  UX improvements                4 hrs    92 hrs
24  Jul 24  SEO + meta tags                4 hrs    96 hrs
25  Jul 25  Performance audit              4 hrs   100 hrs
26  Jul 26  Integration test suite         4 hrs   104 hrs
27  Jul 27  Documentation                 4 hrs   108 hrs
28  Jul 28  Demo video + pitch deck        4 hrs   112 hrs
29  Jul 29  Final bug bash                 4 hrs   116 hrs
30  Jul 30  Investor meeting prep          4 hrs   120 hrs
─────────────────────────────────
TOTAL: 30 days × 4 hrs = 120 hours to investor-ready MVP
```

---

## 🎯 SUCCESS CRITERIA (July 30, 2026)

By July 30, you will have:

1. ✅ **Deployed MVP** — Live at `https://foodly.vercel.app` + API at `https://foodly-api.onrender.com`
2. ✅ **30+ Tests Passing** — Unit, integration, E2E
3. ✅ **Investor Demo** — 3-minute video + live demo
4. ✅ **AI Features Working** — RAG insight, query expansion, report validator, price scraper
5. ✅ **LangSmith Traces** — Proving AI quality with eval scores
6. ✅ **Analytics Live** — Mixpanel tracking, investor metrics dashboard
7. ✅ **Security Hardened** — Rate limiting, CORS, security headers, input sanitization
8. ✅ **Performance Baselines** — p95 < 200ms, cache hit rate > 60%
9. ✅ **Documentation Complete** — README, API docs, AI architecture, deployment guide
10. ✅ **Data Room Ready** — Architecture diagram, benchmarks, test results, AI eval scores

**Ready for investor meetings. 🚀**

---

## 📝 NOTES

- **Current Date:** July 1, 2026 (Day 1 starts today)
- **Daily Commitment:** 4 hours/day (adjust if needed)
- **Flexibility:** If you finish a day early, move to next day. If stuck, ask for help.
- **Priority:** Investor demo > tests > infrastructure > nice-to-haves
- **Skip If Low on Time:** Days 22-30 can be compressed to 5 days if needed

**Bottom line:**
- **Week 1** — Fix bugs, add security, write tests
- **Week 2** — Docker, CI/CD, deploy to cloud, investor demo
- **Week 3** — Monetization features (featured, leaderboard, alerts, analytics)
- **Week 4** — Polish, documentation, demo video, investor prep

**By July 30, you'll have an investor-ready MVP. 🎯**