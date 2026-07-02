# Foodly — Redesigned KPI Plan (4 Hours/Day)
**Starting:** June 26, 2026  
**Daily Commitment:** 4 hours  
**Target:** Investor-ready MVP with working AI features  

---

## 📊 CURRENT STATE ASSESSMENT (June 26, 2026)

### ✅ What's Built & Working
| Component | Status | Notes |
|-----------|--------|-------|
| FastAPI backend with PostgreSQL | ✅ Solid | Auth, meals CRUD, geo-search, admin endpoints |
| Service Layer + Repository Pattern | ✅ Fixed | `MealRepository`, `MealService` properly decoupled |
| Query Expansion (LangChain) | ✅ Built | `query_expansion_chain.py` expands "desi food" → specific meals |
| Report Validator (LangChain) | ✅ Built | `report_validation_chain.py` with statistical pre-check + LLM |
| LangGraph Price Scraper | ✅ Fixed | Retry logic, store to DB, conditional branching working |
| Redis Caching | ⚠️ Partial | `core/cache.py` exists, search + insight cached, but no invalidation |
| AI Insight (agents.py) | ⚠️ Basic | Async ✅ but NO RAG context — no sector stats, no similar meals |
| Price Scraper HITL | ⚠️ Partial | `human_review_node` exists but no checkpointer/interrupt wired |

### ❌ What's Missing (Critical Path)
| Gap | Severity | Why It Blocks You |
|-----|----------|-------------------|
| **RAG Grounded Insight** | 🔴 BLOCKER | Current insight has zero market context — just free-text LLM guess |
| **No tests** | 🔴 BLOCKER | Can't verify any feature works, unprofessional for investors |
| **No LangSmith** | 🔴 BLOCKER | Zero observability, can't measure AI quality or token costs |
| **No rate limiting** | 🟡 HIGH | API is unprotected — 500 req/sec can take it down |
| **No HITL checkpointer** | 🟡 HIGH | Agent state lost on server restart |
| **No WebSocket** | 🟢 LOW (Layer 4) | No real-time notifications |
| **No Docker/CI-CD** | 🟢 LOW (Layer 6) | Not deployable to cloud |

---

## 📅 REDESIGNED 45-DAY KPI PLAN (June 26 → Aug 9, 2026)

### Design Philosophy (4 hrs/day):
1. **Highest investor impact first** — RAG insight, Chat assistant, HITL demo
2. **Quality gates before new features** — Tests and LangSmith before expanding
3. **No over-engineering** — Skip Kafka (overkill for MVP), skip complex multi-agent
4. **Working demos > perfect code** — Ship working features, optimize later

---

### PHASE 1: COMPLETE REMEDIATION SPRINT (3 Days)
**Goal:** Finish the 7-day sprint, close all known bugs.

#### Day 1 — June 26 (Today) 🟢
**🎯 KPI:** Redis cache invalidation working. Cache hit rate measurable.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Add `invalidate_pattern()` to `core/cache.py` — delete keys by pattern | `core/cache.py` |
| 30m | Add cache invalidation hooks in admin approve/reject endpoints | `admin.py`, `reports.py` |
| 30m | Add `X-Cache: HIT | MISS` header middleware | `core/cache.py` |
| 30m | Add cache hit counter (Redis INCR) — `cache_hits:{endpoint}` | `core/cache.py` |
| 1h | Add nearby caching — `nearby:{lat}:{lng}:{radius}:{budget}` 5min TTL | `services/meal.py` |
| 1h | Write a quick cache validation script — `scripts/validate_cache.py` | New file |

**✅ DoD:** Two identical near-API calls → first shows MISS, second shows HIT. Price change invalidates insight cache.

---

#### Day 2 — June 27
**🎯 KPI:** HITL workflow end-to-end. Admin can approve/reject via API.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add PostgreSQL checkpointer to LangGraph | `price_scraper.py` |
| 1h | Wire `interrupt()` in `human_review_node` — pause execution | `price_scraper.py` |
| 1h | Build `POST /api/v1/agent/resume/{thread_id}` endpoint | `endpoints/agent.py` |
| 30m | Build `GET /api/v1/agent/pending` — list paused threads | `endpoints/agent.py` |
| 30m | Test: trigger agent → pause → resume → price updated in DB | Manual test |

**✅ DoD:** Kill server mid-HITL → restart → agent state survives. Admin resume updates meal price.

---

#### Day 3 — June 28
**🎯 KPI:** Sprint complete. All 5 architecture issues closed.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Final polish on report validator — add `ai_validation_score` to DB | `reports.py` |
| 1h | Add `ai_validation_score` visible in admin report list | `admin.py` |
| 1h | Create `backend/app/core/security_headers.py` middleware | New file |
| 30m | Add 5 security headers: X-Content-Type-Options, etc. | `main.py` |
| 30m | Final audit: grep for `print(`, `random.uniform`, `ThreadPoolExecutor` | Whole project |

**✅ DoD:** `grep -r "print(" backend/app/` = 0. `grep -r "random.uniform" backend/` = 0. Security headers on all responses.

---

### PHASE 2: HIGH-VALUE AI FEATURES (6 Days)
**Goal:** Build the 3 features that make Foodly an "AI platform" for investor demos.

#### Day 4 — June 29
**🎯 KPI:** Grounded AI Insight chain built with RAG context retrieval.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Design `InsightResponse` Pydantic schema — verdict, summary, tip, price_percentile, confidence | `ai/schemas/insight.py` (NEW) |
| 1.5h | Build `insight_chain.py` with `RunnableParallel`:
- `retrieve_similar_meals` — pgvector top-5 same category
- `fetch_sector_stats` — avg/min/max for sector
- `fetch_price_history` — last 10 approved reports | `ai/chains/insight_chain.py` (NEW) |
| 1h | Wire into `MealService.get_meal_detail()` replacing old `generate_value_insight` | `services/meal.py` |
| 30m | Add price-aware cache key: `insight:{meal_id}:{price_cents}` | `services/meal.py` |

**✅ DoD:** `GET /meals/1` returns `"verdict": "good_value"`, `"price_percentile": 23`, `"summary"` references sector average price.

---

#### Day 5 — June 30
**🎯 KPI:** LangSmith tracing live on all AI calls. First eval dataset run.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Add LangSmith env vars to `core/config.py` | `core/config.py` |
| 30m | Tag all chains with metadata (meal_id, user_id, endpoint) | `insight_chain.py`, `expansion_chain.py`, `validator_chain.py` |
| 1h | Create `insight_eval_set` — 20 meals with expected verdicts | LangSmith dashboard |
| 1h | Create `search_eval_set` — 15 queries with expected top-3 meals | LangSmith dashboard |
| 1h | Run evaluations, document scores in `docs/ai_eval.md` | New file |

**✅ DoD:** LangSmith shows traces for insight_chain, expansion_chain, validation_chain. Insight verdict_accuracy documented.

---

#### Day 6 — July 1
**🎯 KPI:** Report validator with statistical pre-check + LLM fully integrated.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Add sector_stats pre-check — auto-reject if price > 3x sector avg | `validation_chain.py` |
| 1h | Store `ai_validation_score` in `reports.py` endpoint | `reports.py` |
| 1h | Wire validation score into admin dashboard display | `admin.py` + frontend |
| 1h | Write test script: submit valid + invalid reports, verify auto-reject | `scripts/test_validator.py` |
| 30m | Test: PKR 5 for biryani → 422 auto-rejected. PKR 200 → pending. | Manual |

**✅ DoD:** Submit PKR 5 for biryani → instant 422 with reason, no DB row created. Submit PKR 200 → pending with ai_validation_score in DB.

---

#### Day 7 — July 2
**🎯 KPI:** Rate limiting + security hardening live. API protected.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 45m | Install `slowapi`, configure rate limits per endpoint | `main.py` |
| 45m | Rate limits: global 100/min, login 5/min, search 30/min, reports 10/min, chat 10/min | `core/config.py` |
| 30m | Add `429 Retry-After` header on rate limit responses | Middleware |
| 30m | Security headers middleware — all 5 headers | `core/security_headers.py` |
| 1h | SQL injection test: `'; DROP TABLE meals; --` in search → safe empty results | Manual test |
| 30m | XSS: `bleach.clean()` on string inputs | `reports.py` |

**✅ DoD:** 6th login attempt in 1 min → 429. SQL injection in search → empty results not 500. Security headers on every response.

---

#### Day 8 — July 3
**🎯 KPI:** Conversational Food Assistant (ReAct agent) built and streaming.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Define 5 LangChain tools: `search_nearby_meals`, `filter_meals`, `get_meal_insight`, `get_price_trend`, `semantic_search_meals` | `ai/tools/foodly_tools.py` (NEW) |
| 1.5h | Build ReAct agent with `create_react_agent` + Groq + checkpointer | `ai/graphs/assistant_graph.py` (NEW) |
| 1h | `POST /api/v1/chat` endpoint — SSE streaming with event types: thinking, tool_call, tool_result, token, done | `endpoints/chat.py` (NEW) |
| 1h | Test: "find biryani under 200 near NUST" → agent calls tools → returns results | Manual |

**✅ DoD:** "find biryani under 200 near NUST" → agent calls `search_nearby_meals` → returns ranked results with explanation. Follow-up "what about karahi?" uses conversation context.

---

### PHASE 3: QUALITY & TESTING (5 Days)
**Goal:** Make the codebase testable, measurable, and reliable.

#### Day 9 — July 4
**🎯 KPI:** `pytest` suite with 20+ passing tests. Test coverage > 40%.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Set up pytest config, `conftest.py` with test DB | `tests/conftest.py` |
| 1h | Auth tests: register, login, wrong password → same error, expired token → 401 | `tests/test_auth.py` |
| 1h | Meals tests: list, nearby, search, create (admin only → 403 for non-admin) | `tests/test_meals.py` |
| 1h | Reports tests: submit, approve, reject, duplicate constraint | `tests/test_reports.py` |
| 30m | AI tests: insight chain returns valid verdict, expansion returns list, validator rejects spam | `tests/test_ai.py` |

**✅ DoD:** `pytest tests/` — 20+ tests, 0 failures.

---

#### Day 10 — July 5
**🎯 KPI:** AI safe_invoke wrapper + fallback paths. Circuit breaker for Gemini.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Build `safe_invoke(chain, input, fallback, timeout_s=10)` | `ai/core/safe_invoke.py` (NEW) |
| 1h | Replace all raw `chain.ainvoke()` with `safe_invoke()` — insight, expansion, validator, chat | All chain files |
| 1h | Add circuit breaker: 5 consecutive failures → skip Gemini for 60s | `ai/core/circuit_breaker.py` (NEW) |
| 1h | Test fallbacks: set wrong API keys → verify degraded responses (not 500) | Manual |

**✅ DoD:** Set `GOOGLE_API_KEY=wrong` → all Gemini calls return fallback, zero 500 errors.

---

#### Day 11 — July 6
**🎯 KPI:** AI streaming (SSE) endpoints working. Time-to-first-token < 300ms.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Build `GET /api/v1/meals/{id}/insight/stream` — SSE streaming | `endpoints/meals.py` |
| 1h | Align SSE event format: `thinking`, `tool_call`, `tool_result`, `token`, `done` | `endpoints/chat.py`, `endpoints/agent.py` |
| 1h | Add `request.is_disconnected()` check — stop generator if client disconnects | All SSE endpoints |
| 1h | Cache only final complete insight in Redis (not partial chunks) | `services/meal.py` |

**✅ DoD:** Insight stream — first token < 300ms. Disconnect mid-stream → generator stops (verify in logs).

---

### PHASE 4: INFRASTRUCTURE & DEPLOYMENT (8 Days)
**Goal:** Dockerize, deploy to cloud, measure performance.

#### Day 12 — July 7
**🎯 KPI:** Docker Compose with all services. Zero manual steps to start.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | `backend/Dockerfile` — multi-stage, target < 200MB | `backend/Dockerfile` (NEW) |
| 1h | `frontend/Dockerfile` — 3-stage Next.js standalone | `frontend/Dockerfile` (NEW) |
| 1h | Update `docker-compose.yml` — add postgres, backend, frontend | `docker-compose.yml` |
| 1h | Add health checks, wait-for-it dependencies | `docker-compose.yml` |

**✅ DoD:** `docker-compose up --build` → all services healthy within 60s.

---

#### Day 13 — July 8
**🎯 KPI:** GitHub Actions CI — auto-run tests on PR, fail on coverage < 40%.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | `.github/workflows/ci.yml` — pytest, ruff, eslint on PR | `.github/workflows/ci.yml` (NEW) |
| 1h | `.github/workflows/deploy.yml` — build image, push to registry | `.github/workflows/deploy.yml` (NEW) |
| 1h | Branch protection rules — require CI to pass | GitHub settings |
| 1h | Secrets setup for CI: DATABASE_URL, API keys | GitHub secrets |

**✅ DoD:** PR with failing test → CI fails → merge blocked. Merge to main → image updated.

---

#### Day 14 — July 9
**🎯 KPI:** API deployed to cloud. HTTPS working. Health check passes.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Vercel deployment for frontend — connect GitHub repo | Vercel dashboard |
| 1h | Railway/Render deployment for backend with PostgreSQL + Redis | Railway/Render dashboard |
| 1h | Set up custom domain + HTTPS | DNS + SSL |
| 30m | Set up all environment variables in cloud dashboard | Cloud dashboard |
| 30m | Test: `GET /health` → `{ "status": "ok", "db": "connected", "redis": "connected" }` | curl test |

**✅ DoD:** `https://api.foodly.pk/health` returns 200. Frontend loads at custom URL.

---

#### Day 15 — July 10
**🎯 KPI:** Structured logging + basic monitoring. 99% error rate visibility.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Set up `structlog` — JSON logs with timestamp, level, service, endpoint, latency, status_code | `core/logging.py` (NEW) |
| 1h | Add `prometheus-fastapi-instrumentator` — HTTP metrics, WS connections | `main.py` |
| 1h | Set up Sentry for error tracking — `sentry-sdk` with 0.1 sample rate | `main.py` |
| 1h | Test: trigger 500 error → Sentry shows stack trace within 30s | Manual |

**✅ DoD:** Trigger intentional 500 → Sentry captures it. Logs are structured JSON in CloudWatch/Render logs.

---

#### Day 16 — July 11
**🎯 KPI:** k6 baseline benchmark — p95 latency documented.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Install k6, write `load_test.js` — test `/meals`, `/nearby`, `/search` | `load_test.js` (NEW) |
| 1.5h | Run k6: 50 VUs × 60s. Record p50, p95, p99, req/s, error rate | Terminal |
| 1h | Separate AI test: 10 VUs × 60s on `/insight`, `/chat` | Terminal |
| 30m | Document results in `docs/benchmarks.md` | New file |

**✅ DoD:** `/nearby` p95 < 200ms (cached). `/insight` time-to-first-token < 300ms. Error rate < 1%.

---

#### Day 17 — July 12
**🎯 KPI:** Cache optimization. Token costs reduced by 40%+.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 1h | Add cache hit rate logging — measure actual hit rates per endpoint | `core/cache.py` |
| 1h | Optimize TTLs based on hit rates — extend insight cache to 48h, reduce search to 10min | `services/meal.py` |
| 1h | Add cache warming on meal create/update — pre-compute and cache insight | `services/meal.py` |
| 1h | Measure token cost before/after using LangSmith token counts | LangSmith dashboard |

**✅ DoD:** Cache hit rate > 60% on search and insight. Token cost per 100 insight calls reduced by 40%+.

---

#### Day 18 — July 13
**🎯 KPI:** First full investor demo flow working end-to-end.
**⏱ 4 hours:**
| Time | Task | File |
|------|------|------|
| 30m | Stitch demo flow: register → search "biryani F-7" → get RAG insight → chat "find cheap near NUST" → save meal → submit report → admin approves → price updated | All systems |
| 1h | Record 2-minute screen demo (no voiceover needed) | Screen recorder |
| 1h | Update `README.md` with architecture overview, local setup, AI features | `README.md` |
| 1h | Prepare data room: architecture diagram, key metrics, load test results, AI eval scores | `docs/investor/` folder |
| 30m | Rehearse demo — ensure < 2 mins, zero errors | Dry run |

**✅ DoD:** Full demo flow works in production. README updated. Data room ready for investors.

---

### PHASE 5: MONETIZATION & GROWTH (27 Days)
**Goal:** Revenue features, analytics, and polish.

#### Day 19 — July 14: Featured listings + OG share cards
#### Day 20 — July 15: Reporter leaderboard + Meal of the Day
#### Day 21 — July 16: Price alerts (email when meal drops below threshold)
#### Day 22 — July 17: Premium plan stub (`users.plan: free | premium`)
#### Day 23 — July 18: Mixpanel analytics — search queries, meal views, saves, reports, chat
#### Day 24 — July 19: Admin analytics dashboard (top searches, report funnel)
#### Day 25 — July 20: Feedback widget (Tally embed after 5th session)
#### Day 26 — July 21: NPS survey email to all registered users (Resend)
#### Day 27 — July 22: Investor metrics dashboard (`/admin/investor-metrics`)
#### Day 28 — July 23: PDF export for investor meetings
#### Day 29 — July 24: A/B test: vector search vs vector + query expansion
#### Day 30 — July 25: Fix top UX issues from dogfooding
#### Day 31 — July 26: Performance optimization — audit slow queries
#### Day 32 — July 27: More seed data — target 500 meals in DB
#### Day 33-35 — July 28-30: Final integration test + full suite pass
#### Day 36-38 — July 31-Aug 2: WebSocket layer (live notifications, search suggestions)
#### Day 39-41 — Aug 3-5: OWASP ZAP security scan — fix HIGH findings
#### Day 42-45 — Aug 6-9: Final polish, demo video, investor meeting prep

---

## 📊 CONSENSUS KPIs (Aug 9, 2026 — Final Target)

| KPI | Target | Current | Gap |
|-----|--------|---------|-----|
| Demos & Investor |
| Demo flow working end-to-end | ✅ Pass | ❌ Broken | 🔴 NEEDS WORK |
| Investor metrics dashboard | ✅ Live | ❌ Missing | 🔴 NEEDS BUILD |
| Data room (docs + tests + benchmarks) | ✅ Complete | ❌ Missing | 🔴 NEEDS BUILD |
| AI Features |
| LangGraph agents live | 2 (price + HITL) | 1 (partial) | 🟡 Close |
| LangChain chains live | 4 (insight + expansion + validator + assistant) | 2 (expansion + validator) | 🟡 2 more |
| Insight verdict_accuracy | ≥ 75% | 0% (unbuilt) | 🔴 BUILD FIRST |
| Search recall@5 | ≥ 80% | Not measured | 🟡 Need eval |
| Quality |
| `pytest` pass rate | 100% | 0% (no tests) | 🔴 BUILD SUITE |
| LangSmith traces | All AI calls | 0% | 🔴 INTEGRATE |
| AI error rate | < 0.5% | Unknown | 🟡 Need measurement |
| Security |
| Rate limiting | Active | ❌ None | 🔴 MUST ADD |
| OWASP HIGH findings | 0 | Unknown | 🟡 Need scan |
| Performance |
| `/nearby` p95 (cached) | < 200ms | Unknown | 🟡 Need benchmark |
| `/insight` time-to-first-token | < 300ms | Unknown | 🟡 Need benchmark |
| Cache hit rate | > 60% | Unknown | 🟡 Need measurement |
| Infrastructure |
| Docker Compose up | One command | ❌ Partial | 🟡 Need completion |
| Cloud deployment | HTTPS live | ❌ Not deployed | 🟡 Railway/Render |
| CI/CD | Auto-deploy | ❌ Not built | 🟡 GitHub Actions |

---

## ⚡ THE 80/20 RULE — What Gets You 80% of Investor Value in 20% of Time

If you have **only 10 more days**, focus on this:

### Week 1 (Jun 26 — Jul 2): The "Investor Demo" Sprint
1. **Jun 26** — Finish Redis cache (invalidation + monitoring)
2. **Jun 27** — HITL checkpointer (the most impressive demo feature)
3. **Jun 28** — Security + sprint cleanup
4. **Jun 29** — 🔥 **RAG Grounded Insight** (highest AI value)
5. **Jun 30** — 🔥 **LangSmith tracing** (prove AI quality)
6. **Jul 1** — Report validator polish
7. **Jul 2** — Rate limiting + security

### Week 2 (Jul 3 — Jul 9): The "Ship It" Sprint
8. **Jul 3** — 🔥 **Chat Assistant (ReAct agent)** (2nd most impressive demo)
9. **Jul 4** — Test suite (basic coverage)
10. **Jul 5** — AI fallbacks + circuit breaker
11. **Jul 6** — SSE streaming for insight + chat
12. **Jul 7** — Docker Compose
13. **Jul 8** — CI/CD (GitHub Actions)
14. **Jul 9** — Deploy to production (Railway/Vercel)

**After 14 days (Jul 9), you'll have:**
- ✅ Working HITL demo
- ✅ RAG-grounded AI insight with real market data
- ✅ Conversational food assistant
- ✅ LangSmith traces proving AI quality
- ✅ Rate-limited, secure API
- ✅ Deployed to cloud with HTTPS
- ✅ Basic test suite

**That's enough for investor conversations.**

---

## 🚨 CRITICAL: DON'T BUILD THESE (Yet)

| Feature | Original Day | Why Skip Now |
|---------|--------------|--------------|
| Kafka (Layer 5) | Days 32-38 | Overkill for MVP — Redis Pub/Sub is fine at current scale |
| Multi-agent supervisor | Day 16 | 50 parallel scrapers = too complex for 4 hrs/day |
| Personalized feed | Day 15 | Requires many users with history — you don't have that yet |
| WebSocket server | Days 27-31 | SSE works for demos, add WS when you have 100+ concurrent users |
| A/B testing framework | Day 54 | Premature optimization — you need users first |
| OWASP ZAP active scan | Day 44 | Passive security (headers + rate limits) is enough for demo |

---

## 📈 TIME BUDGET TRACKER (4 hours/day)

```
Day    Date      Focus                         Hours   Cumulative
──────────────────────────────────────────────────────────────
  1  Jun 26  Redis caching                    4 hrs     4 hrs
  2  Jun 27  HITL workflow                    4 hrs     8 hrs
  3  Jun 28  Sprint cleanup + security        4 hrs    12 hrs
  4  Jun 29  RAG insight chain                4 hrs    16 hrs
  5  Jun 30  LangSmith + eval datasets        4 hrs    20 hrs
  6  Jul  1  Report validator integration     4 hrs    24 hrs
  7  Jul  2  Rate limiting + security         4 hrs    28 hrs
  8  Jul  3  Chat assistant (ReAct)           4 hrs    32 hrs
  9  Jul  4  Test suite (20+ tests)           4 hrs    36 hrs
 10  Jul  5  AI fallbacks + circuit breaker   4 hrs    40 hrs
 11  Jul  6  SSE streaming                    4 hrs    44 hrs
 12  Jul  7  Docker Compose                   4 hrs    48 hrs
 13  Jul  8  CI/CD pipeline                   4 hrs    52 hrs
 14  Jul  9  Deploy to cloud                  4 hrs    56 hrs
 15  Jul 10  Structured logging + Sentry      4 hrs    60 hrs
 16  Jul 11  k6 load testing                  4 hrs    64 hrs
 17  Jul 12  Cache optimization + cost save   4 hrs    68 hrs
 18  Jul 13  Demo video + data room           4 hrs    72 hrs
 19-45  Jul 14-Aug 9  Monetization + Growth  108 hrs   180 hrs
──────────────────────────────────────────────────────────────
TOTAL: 45 days × 4 hrs = 180 hours to investor-ready MVP
```

---

**Bottom line:** 
- **Today (Jun 26)** — Finish Redis cache invalidation + monitoring
- **This week** — Finish remediation sprint → Build RAG insight → LangSmith
- **Next week** — Chat assistant → Tests → Deploy to cloud
- **By Jul 13** — Investor demo ready with working AI features