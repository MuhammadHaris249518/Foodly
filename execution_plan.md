# Foodly — 60-Day Production Engineering Sprint

**Version:** 5.0 · June 2026
**Author:** Muhammad Haris
**Target:** PKR 15M / USD 50K Seed Round
**Daily Commitment:** 3–5 hours/day

---

## Architecture Progression

```
Layer 1  (Days 01–08)  →  Monolith MVP            Clean API + DB schema + PostGIS + pgvector
Layer 2  (Days 09–20)  →  AI Workflows Layer       LangGraph agents + LangChain RAG + HITL + multi-agent
Layer 3  (Days 21–26)  →  Performance Layer        Redis caching + query optimization + rate limiting
Layer 4  (Days 27–31)  →  Real-time Layer          WebSockets + live price/report/agent updates
Layer 5  (Days 32–38)  →  Event-driven Layer       Kafka + async workers + agent pipeline orchestration
Layer 6  (Days 39–50)  →  Production Layer         Docker + CI/CD + AWS + observability + LangSmith
Layer 7  (Days 51–60)  →  Growth & Investor Prep   Analytics + monetization + pitch-ready metrics
```

---

## Current Codebase Baseline (What Already Exists)

| Module | File | Status | Problem |
|--------|------|--------|---------|
| LangGraph price scraper | `backend/ai/agents/price_scraper.py` | Working | Conditional edge always returns `"end"` — retry is dead code. Never writes to DB. |
| LangChain AI insight | `backend/ai/agents/agents.py` | Working | Single-shot prompt, zero market context, no grounding |
| Tavily web search tool | `backend/ai/tools/search_tools.py` | Working | Used only by price scraper |
| Google Gemini embeddings | `backend/app/services/embeddings.py` | Working | Solid |
| Price history | `backend/app/api/endpoints/meals.py:134` | **Broken** | `random.uniform` — fake data shown to users |
| AI insight timeout | `backend/app/api/endpoints/meals.py:149` | Fragile | `ThreadPoolExecutor` with 1.5s hard timeout — not production safe |
| Semantic search | `backend/app/api/endpoints/meals.py:34` | Working | No query expansion — low recall |

---

## Global Engineering Standards (Enforced Every Day)

| Concern | Standard |
|---------|----------|
| API design | RESTful, versioned (`/api/v1/`), consistent error shape `{ "error": { "code": "", "message": "" } }` |
| Validation | Pydantic v2 DTOs on every endpoint — no raw dicts in handlers |
| Service layer | Route → Service → Repository — no DB calls in route handlers |
| DB access | SQLAlchemy 2.0 async sessions — parameterized queries only |
| Security | JWT HS256, bcrypt cost 12, no secrets hardcoded |
| AI calls | Every LangGraph/LangChain call must have a timeout + graceful fallback |
| Tests | 1 happy-path + 1 edge-case test per feature/day minimum |

---

## LAYER 1 — MONOLITH MVP (Days 1–8)

### DAY 1 — Project Architecture + DB Schema

**Prerequisites:**
- Understand service-layer pattern before writing a line: Route → Service → Repository. Violations here compound through all 60 days.

**KPI:** PostgreSQL schema live, all 6 tables created, FastAPI returns `200` on `/health`.

**Tasks:**
1. Enforce folder structure:
   ```
   backend/
   ├── app/
   │   ├── api/v1/endpoints/    ← route handlers only
   │   ├── core/                ← config.py, security.py, database.py
   │   ├── models/              ← SQLAlchemy ORM models
   │   ├── schemas/             ← Pydantic DTOs
   │   ├── services/            ← business logic
   │   ├── repositories/        ← DB queries only
   │   └── main.py
   ├── ai/
   │   ├── agents/              ← LangGraph graphs
   │   ├── chains/              ← LangChain LCEL chains
   │   ├── tools/               ← LangChain tools (Tavily, DB, search)
   │   ├── graphs/              ← complex multi-node graphs
   │   └── state/               ← TypedDict state schemas
   ```
2. Configure `core/config.py` with `pydantic-settings` — all secrets from `.env`.
3. Configure `core/database.py` — SQLAlchemy 2.0 async engine + `AsyncSession`.
4. Full PostgreSQL schema:
   - `users` — id, email, hashed_password, role, karma_score, created_at
   - `restaurants` — id, name, address, sector, location `GEOGRAPHY(POINT,4326)`, is_featured
   - `meals` — id, restaurant_id, name, description, price, category, image_url, confidence_score, embedding `VECTOR(1536)`, is_featured, created_at, updated_at
   - `saved_meals` — user_id, meal_id, saved_at (composite PK)
   - `price_reports` — id, meal_id, reporter_id, reported_price, status (pending/approved/rejected), ai_validation_score, created_at
   - `pending_verifications` — id, meal_id, source (community/web_agent), raw_data JSONB, extracted_price, confidence, status, agent_thread_id, created_at
5. Run Alembic migration. Add extensions: `postgis`, `vector`.
6. Spatial index: `CREATE INDEX restaurants_location_gix ON restaurants USING GIST(location);`
7. HNSW index: `CREATE INDEX ON meals USING hnsw (embedding vector_cosine_ops);`
8. Frontend: scaffold `app/`, `components/`, `lib/api.ts`, `hooks/`, `types/`.

**Output:** Running stack, all DB tables, frontend scaffolded.

**DoD:**
- `alembic upgrade head` runs clean
- `SELECT COUNT(*) FROM pg_extension WHERE extname IN ('postgis','vector');` returns 2
- `GET /health` → `{ "status": "ok", "db": "connected" }`
- No hardcoded secrets anywhere in codebase

---

### DAY 2 — User Authentication (JWT + bcrypt)

**Prerequisites:** Stateless auth only — no sessions. Required for horizontal scaling in Layer 6.

**KPI:** Register → login → protected `/me` flow working end-to-end.

**Tasks:**
1. `POST /api/v1/auth/register` — bcrypt cost 12, unique email enforced, never return password hash.
2. `POST /api/v1/auth/login` — same error message for wrong email and wrong password (prevents user enumeration).
3. JWT payload: `{ sub: user_id, role: user.role, jti: uuid4(), exp: now+7d }`. Sign with `SECRET_KEY` (min 32 bytes).
4. `GET /api/v1/auth/me` — `Depends(get_current_user)` decodes + validates JWT.
5. `POST /api/v1/auth/logout` — add `jti` to Redis revocation set with TTL matching token expiry.
6. `core/security.py`: `create_token()`, `decode_token()`, `hash_password()`, `verify_password()`.
7. Frontend `lib/api.ts` — Axios client, attach JWT from `localStorage` on every request.
8. Tests: register success, login success, wrong password → same error, expired token → 401, revoked token → 401.

**Output:** Full auth system with token revocation.

**DoD:**
- Wrong password and wrong email return identical `401` response body
- Logout → reuse same token → `401 token revoked`
- bcrypt hash in DB (not plaintext) — verify with `SELECT hashed_password FROM users LIMIT 1`

---

### DAY 3 — Core Meals API (CRUD + Service Layer)

**KPI:** Full meals CRUD with DTOs, service layer, repository pattern. Pagination working.

**Tasks:**
1. `MealRepository`: `get_by_id`, `list_paginated`, `create`, `update`, `soft_delete`, `search_by_name`.
2. `MealService`: orchestrates repo, enforces business rules (confidence default = 100 on create).
3. Endpoints: `GET /meals` (paginated + filters), `GET /meals/{id}`, `POST /meals` (admin), `PUT /meals/{id}` (admin), `DELETE /meals/{id}` (admin soft-delete).
4. Consistent pagination wrapper: `{ data, total, page, size, pages }`.
5. `MealResponse` DTO — never expose `embedding` column or internal fields.
6. Role guard: `Depends(require_role("admin"))` on write endpoints.
7. Frontend: homepage renders meal cards from `GET /api/v1/meals`.

**Output:** Full CRUD API. Service layer enforced. Frontend renders DB meals.

**DoD:**
- `POST /meals` with non-admin JWT → `403`
- `?page=2&size=5` returns correct subset
- `embedding` field never appears in any API response

---

### DAY 4 — PostGIS Geo-Search + Saved Meals

**KPI:** `/nearby` returns distance-sorted meals using spatial index in < 300ms. Save toggle persists.

**Tasks:**
1. `GET /api/v1/meals/nearby?lat=&lng=&radius_km=&max_price=&category=&page=&size=`:
   - `ST_DWithin` with spatial index, `ST_DistanceSphere` for sort.
   - Add `distance_km` to response.
2. Composite index: `meals(category, price)`.
3. `EXPLAIN ANALYZE` — confirm `Index Scan using restaurants_location_gix` (not Seq Scan).
4. `POST /api/v1/meals/{id}/save` — toggle (insert if absent, delete if present).
5. `GET /api/v1/users/me/saved` — paginated saved meals.
6. Frontend: map panel click → calls `/nearby`. Bookmark icon toggle on meal cards.

**Output:** Geo-filtered search. Saved meals system.

**DoD:**
- `EXPLAIN ANALYZE` shows spatial index scan
- Double-toggle save → 0 rows in `saved_meals` for that pair
- Response includes `distance_km` on every nearby result

---

### DAY 5 — pgvector Semantic Search + Foodly Score

**KPI:** Semantic search returns relevant results. Foodly Score on every meal response.

**Tasks:**
1. Embedding pipeline: on meal create/update, call Gemini `text-embedding-004` → store in `meals.embedding VECTOR(1536)`.
2. `GET /api/v1/meals/search?q=`: embed query → `ORDER BY embedding <=> :vec LIMIT 20` → ILIKE fallback if similarity score > 0.8.
3. Foodly Score in `MealService.compute_score(meal, user_lat, user_lng, user_budget)`:
   ```python
   budget_fit  = max(0, 1 - price / budget) * 100   # weight 0.40
   proximity   = max(0, 100 - distance_km * 20)      # weight 0.35
   confidence  = meal.confidence_score                # weight 0.25
   score = budget_fit*0.40 + proximity*0.35 + confidence*0.25
   ```
4. `foodly_score` in every `MealResponse`. Default sort for `/nearby` is `foodly_score DESC`.
5. Batch-embed all existing seeded meals: `scripts/embed_all_meals.py`.

**Output:** Semantic search. Foodly Score on all responses.

**DoD:**
- "student budget lunch" returns meals under PKR 200, ranked by score
- `foodly_score` is always 0–100, never null
- HNSW index scan visible in `EXPLAIN` output

---

### DAY 6 — Community Price Reports + Confidence System

**KPI:** Submit → pending → admin approve/reject → confidence updated. Full cycle < 2 min.

**Tasks:**
1. `POST /api/v1/meals/{id}/reports` — authenticated. Insert into `price_reports(status=pending)`. Decay: `confidence -= 5` (floor 0).
2. `GET /api/v1/meals/{id}/reports` — approved reports as price history (real data, not random).
3. Admin: `GET /admin/reports?status=pending`, `PATCH /admin/reports/{id}/approve`, `PATCH /admin/reports/{id}/reject`.
4. Approve: update meal price, `confidence += 10` (ceil 100), `reporter.karma_score += 1`.
5. Reject: `confidence += 5`, `reporter.karma_score -= 1` (floor 0).
6. DB constraint: one pending report per user per meal.
7. **Fix `meals.py:134`** — delete `random.uniform` price history entirely. Return real approved reports from DB. If < 2 approved reports exist, return what's there (do not fabricate data).

**Output:** Community reporting. Real price history from DB. Confidence system.

**DoD:**
- Submit report → confidence drops from 100 to 95 immediately
- `GET /meals/{id}` `price_history` contains only real approved report rows
- `random.uniform` and `random` import removed from `meals.py`

---

### DAY 7 — Admin Dashboard API + Seed Data

**KPI:** Admin API complete with real stats. 200+ real Islamabad meals seeded.

**Tasks:**
1. `GET /api/v1/admin/stats` — `{ total_meals, total_users, pending_reports, avg_confidence }`. Cache 1 min in Redis.
2. `GET /api/v1/admin/meals` — with `report_count`, `confidence_score`, `last_reported_at`.
3. `POST /api/v1/admin/reports/bulk-approve` — body `{ ids: [...] }` — single DB transaction.
4. Frontend admin page: stats cards + pending reports table + approve/reject buttons.
5. `scripts/seed_islamabad.py` — 200+ real restaurants across F-6, F-7, F-10, G-9, Blue Area, Saddar, NUST, COMSATS, QAU. Real GPS coordinates. Real prices. Auto-generate embeddings.

**Output:** Admin API. 200+ seeded meals. Real data in DB.

**DoD:**
- Non-admin JWT on `/admin/*` → `403`
- `SELECT COUNT(*) FROM meals` ≥ 200
- All meals have non-null `embedding` column

---

### DAY 8 — Layer 1 Integration Tests + Baseline Benchmarks

**KPI:** Full integration test suite passes. Baseline latencies documented.

**Tasks:**
1. `pytest` + `httpx.AsyncClient` covering: auth lifecycle, meals CRUD, geo-search, semantic search, reports, admin.
2. `EXPLAIN ANALYZE` on 5 heaviest queries — document ms timings in `docs/benchmarks.md`.
3. Verify all API responses match Pydantic DTOs exactly.
4. Fix `ThreadPoolExecutor` in `meals.py:149` — replace with proper `asyncio.wait_for()` wrapping an async Gemini call. No thread hacks.

**Output:** Integration test suite. Baseline benchmarks. Thread-safe AI calls.

**DoD:**
- `pytest tests/integration/` — 0 failures
- No `ThreadPoolExecutor` in any AI call path
- Benchmarks committed to `docs/benchmarks.md`

---

## LAYER 2 — AI WORKFLOWS LAYER (Days 9–20)

> This layer transforms Foodly from "has some AI" to "AI-first platform." Every workflow is built with LangGraph or LangChain LCEL — no ad-hoc prompts, no fake data, no synchronous blocking calls.

---

### DAY 9 — Fix Existing AI Code + LangGraph State Design

**Prerequisites:**
- Read `price_scraper.py` lines 39–53: the `should_continue` function always returns `"end"`. The retry branch is unreachable. This is the first fix.
- Read `agents.py`: `generate_value_insight` calls `llm.invoke()` synchronously inside a `ThreadPoolExecutor`. This is not production-safe.
- Understand LangGraph state: `AgentState` is the single source of truth flowing through every node. Design it before building any graph.

**KPI:**
- `price_scraper.py` conditional edge actually retries on low confidence. `generate_value_insight` is async. New shared `AgentState` schema covers all planned agents.

**Tasks:**
1. **Fix `price_scraper.py:should_continue`** — implement real branching:
   ```python
   def should_continue(state: AgentState) -> str:
       data = state.get("extracted_data")
       if data and data.price_pkr > 0 and data.confidence >= 50:
           return "store"          # go to new store node
       if state.get("iterations", 0) >= 3:
           return "end"            # give up after 3 tries
       return "retry"              # generate new query and search again
   ```
2. Add `retry_node` — uses Groq to generate a refined search query:
   ```python
   def retry_node(state: AgentState) -> AgentState:
       # Ask LLM: "previous query returned low-confidence results. Generate a better query."
       refined_query = refine_chain.invoke({"original": state["search_query"], "results": state["search_results"]})
       return {"search_query": refined_query, "search_results": "", "extracted_data": None}
   ```
3. Add `store_node` — inserts result into `pending_verifications` table.
4. Redesign `AgentState` in `ai/state/base.py` to cover all planned agents:
   ```python
   class AgentState(TypedDict):
       search_query: str
       search_results: str
       extracted_data: Optional[ExtractedPrice]
       iterations: int
       meal_id: Optional[int]
       thread_id: Optional[str]         # for HITL resume
       validation_passed: Optional[bool]
       retry_reason: Optional[str]
   ```
5. **Fix `agents.py:generate_value_insight`** — convert to `async def`, use `await llm.ainvoke()`. Remove `ThreadPoolExecutor` from `meals.py`.
6. Wire fixed graph: `search → extract → [retry | store | end]`.

**Output:** Fixed price scraper with real retry logic and DB store. Async AI insight. Shared state schema.

**DoD:**
- Trigger agent with a vague query ("food") → retries with refined query (check logs)
- Successful extraction → row appears in `pending_verifications`
- `generate_value_insight` is now `async`, no `ThreadPoolExecutor` anywhere
- `AgentState` has `thread_id` and `validation_passed` fields

---

### DAY 10 — Grounded AI Insight with RAG (LangChain LCEL)

**Prerequisites:**
- Understand why the current insight is wrong: it receives `name`, `price`, `location` but has no idea what the market average is, what similar meals cost, or whether PKR 350 is cheap or expensive in that sector.
- RAG = Retrieve context first → build grounded prompt → generate insight.

**KPI:**
- AI insight now includes sector price comparison, value verdict, and market context. Response is structured JSON, not free text.

**Tasks:**
1. Create `ai/chains/insight_chain.py` using LangChain LCEL:
   ```python
   insight_chain = (
       RunnableParallel({
           "similar_meals": retrieve_similar_meals,   # pgvector: top 5 meals same category
           "sector_stats":  fetch_sector_stats,       # DB: avg/min/max price for sector
           "price_history": fetch_price_history,      # DB: last 10 approved reports
           "meal":          RunnablePassthrough()
       })
       | build_grounded_prompt          # PromptTemplate with all context injected
       | ChatGoogleGenerativeAI(model="gemini-2.0-flash")
       | structured_output_parser       # parse to InsightResponse Pydantic model
   )
   ```
2. `InsightResponse` Pydantic schema:
   ```python
   class InsightResponse(BaseModel):
       verdict: Literal["best_deal", "good_value", "fair", "overpriced"]
       summary: str          # 1–2 sentences grounded in real data
       tip: str              # actionable advice ("Go before 2pm for smaller crowds")
       price_percentile: int # e.g. 23 means "cheaper than 77% of similar meals nearby"
       confidence: int       # 0–100
   ```
3. `retrieve_similar_meals` tool: takes `(meal_id, category, embedding)` → returns 5 nearest meals by vector similarity.
4. `fetch_sector_stats` tool: SQL query returning `{ avg_price, min_price, max_price, meal_count }` for that category + sector.
5. Replace `generate_value_insight` call in `meals.py` with `await insight_chain.ainvoke(meal_context)`.
6. Cache result in Redis: key `insight:{meal_id}`, TTL 24 hours. Invalidate on price change.

**Output:** `insight_chain.py`. Structured grounded AI insight. Context-aware verdict.

**DoD:**
- Insight for a PKR 150 biryani includes `price_percentile` showing it's cheaper than X% of similar meals
- `verdict` is one of the 4 enum values — never raw text
- Second call returns `X-Cache: HIT` (no Gemini call)
- Insight references actual sector average price in the `summary` field

---

### DAY 11 — Smart Query Expansion (LangChain LCEL)

**Prerequisites:**
- Current problem in `meals.py:34`: user searches "desi food" → ILIKE finds nothing because no meal is literally named "desi food". Semantic search helps but a single embedding misses breadth.
- Query expansion = ask LLM to generate 5 related terms → embed each → union search → better recall.

**KPI:**
- Search "desi food" returns biryani, karahi, nihari, haleem results. Search recall improves measurably for 10 test queries.

**Tasks:**
1. Create `ai/chains/query_expansion_chain.py`:
   ```python
   expansion_chain = (
       ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
       | expansion_prompt    # "List 5 specific Pakistani meal names that match '{query}'. Return JSON array only."
       | JsonOutputParser()
   )
   ```
2. `SearchService.semantic_search(query)`:
   ```python
   # Step 1: expand query
   expanded_terms = await expansion_chain.ainvoke({"query": query})  # ["biryani", "karahi", ...]

   # Step 2: embed all terms (parallel)
   embeddings = await asyncio.gather(*[embed_query(t) for t in [query] + expanded_terms])

   # Step 3: union search — find meals near ANY of the embeddings
   results = await meal_repo.vector_union_search(embeddings, limit=20)

   # Step 4: deduplicate + rerank by Foodly Score
   return deduplicate_and_rerank(results)
   ```
3. `vector_union_search` in `MealRepository` — one SQL query using `UNION` of similarity searches.
4. Replace the existing search logic in `meals.py:34` with `SearchService.semantic_search()`.
5. Evaluate: run 10 test queries before/after. Document recall improvement in `docs/ai_eval.md`.

**Output:** Query expansion chain. Union vector search. Measurable recall improvement.

**DoD:**
- "desi food" returns ≥ 5 relevant Pakistani meals
- "cheap student lunch" returns meals < PKR 200
- Expansion LLM call completes in < 500ms (Groq is fast)
- Before/after recall documented for 10 test queries

---

### DAY 12 — AI Report Validator (LangChain Chain)

**Prerequisites:**
- Currently every price report goes straight to admin. An auto-validator reduces admin workload and catches spam (PKR 5 for biryani, PKR 50,000 for a chai).
- Validate before inserting into `price_reports`. High-confidence invalid → auto-reject. Borderline → admin queue.

**KPI:**
- Obvious invalid reports auto-rejected without admin. Report validator runs in < 1 second. Admin queue contains only borderline/valid reports.

**Tasks:**
1. Create `ai/chains/report_validation_chain.py`:
   ```python
   validation_chain = (
       RunnableParallel({
           "report":        RunnablePassthrough(),
           "meal_context":  fetch_meal_and_sector_stats,   # current price + sector avg
       })
       | validation_prompt   # "Is PKR {reported_price} a realistic price for {meal_name} in {sector}?"
       | ChatGroq(model="llama-3.3-70b-versatile")
       | structured_output_parser  # → ValidationResult(valid, confidence, rejection_reason)
   )
   ```
2. `ValidationResult` schema:
   ```python
   class ValidationResult(BaseModel):
       valid: bool
       confidence: int          # 0–100
       rejection_reason: Optional[str]
       price_range_expected: str   # e.g. "PKR 150–400 for biryani in F-7"
   ```
3. Statistical pre-check before LLM call (fast path):
   - If `reported_price > 3 × sector_avg` OR `reported_price < 0.1 × sector_avg` → auto-reject without LLM call (save tokens).
   - Otherwise → run LLM validation.
4. Modify `POST /api/v1/meals/{id}/reports`:
   - Run `validation_chain.ainvoke()` before inserting.
   - Store `ai_validation_score` in `price_reports` row.
   - If `valid=False` and `confidence >= 85` → auto-reject, return `422` with reason.
   - If `valid=False` and `confidence < 85` → insert with `status=needs_review` flag for admin.
5. Store `rejection_reason` so admin can see why auto-rejected (audit trail).

**Output:** AI report validator. Auto-rejection for obvious spam. `ai_validation_score` on every report.

**DoD:**
- Submit report: PKR 5 for biryani → `422` with rejection reason, no DB insert
- Submit report: PKR 200 for biryani (valid) → inserts into pending normally
- Statistical pre-check fires before LLM for price > 3× avg (verify via logs)
- `ai_validation_score` visible in admin report list

---

### DAY 13 — Human-in-the-Loop Verification (LangGraph Interrupt)

**Prerequisites:**
- Understand LangGraph checkpointing: the graph state is persisted to a checkpointer (PostgreSQL or Redis) so execution can pause and resume across HTTP requests.
- The web agent finds a price → graph pauses at "admin review" node → admin approves via API → graph resumes and applies the price update.
- This replaces the disconnected `pending_verifications` table + separate approval endpoint with a single durable workflow.

**KPI:**
- Web agent result pauses in LangGraph interrupt state. Admin approves via `POST /agent/resume/{thread_id}`. Graph resumes and updates meal price. Full cycle verifiable end-to-end.

**Tasks:**
1. Add PostgreSQL checkpointer to LangGraph:
   ```python
   from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
   checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
   graph = build_price_agent().compile(checkpointer=checkpointer)
   ```
2. Add `human_review_node` to price agent graph — uses `interrupt()`:
   ```python
   def human_review_node(state: AgentState) -> AgentState:
       interrupt({
           "message": "Admin review required",
           "meal_id": state["meal_id"],
           "extracted_price": state["extracted_data"].price_pkr,
           "confidence": state["extracted_data"].confidence,
           "source_url": state["extracted_data"].source_url
       })
       # Execution pauses here. Resumes when admin calls /agent/resume/{thread_id}
       return state
   ```
3. Updated graph edges:
   ```
   search → extract → validate_price
     → [confidence >= 70] → human_review_node → apply_price_update → notify_reporter → END
     → [confidence < 70 and iterations < 3] → retry_node → search
     → [iterations >= 3] → store_as_low_confidence → END
   ```
4. New endpoint `POST /api/v1/agent/resume/{thread_id}`:
   - Body: `{ "decision": "approve" | "reject", "admin_note": "..." }`
   - Resume graph: `graph.ainvoke(Command(resume=decision), config={"configurable": {"thread_id": thread_id}})`
5. `GET /api/v1/agent/pending` — list all graphs currently paused at `human_review_node` (query checkpointer).
6. Store `agent_thread_id` in `pending_verifications` row — links DB record to LangGraph thread.
7. Frontend admin page: show paused verifications with approve/reject buttons → calls `/agent/resume/{thread_id}`.

**Output:** HITL verification workflow. Durable LangGraph state. Admin resume endpoint.

**DoD:**
- Trigger agent → graph pauses at `human_review_node` → `GET /agent/pending` shows the paused thread
- Admin calls `POST /agent/resume/{id}` with `approve` → graph resumes → meal price updated → row removed from pending
- Kill and restart the FastAPI server → paused graph state survives (checkpoint in PostgreSQL)
- Frontend shows pending verifications from checkpointer, not just `pending_verifications` table

---

### DAY 14 — Conversational Food Assistant — Tools + ReAct Graph (LangGraph)

**Prerequisites:**
- This is the highest-value AI feature for users and investors. "Ask Foodly anything about food in Islamabad."
- ReAct pattern: Reason → Act (call tool) → Observe (get tool result) → Reason again. LangGraph manages this loop.
- Define all tools as LangChain `@tool` decorated functions before building the graph.

**KPI:**
- User query "find something under PKR 200 near NUST not biryani" → agent calls 2–3 tools → returns ranked meal list with explanation. Agent reasoning visible in SSE stream.

**Tasks:**
1. Define tools in `ai/tools/foodly_tools.py`:
   ```python
   @tool
   async def search_nearby_meals(lat: float, lng: float, radius_km: float, max_price: float) -> list[dict]:
       """Search for meals near a location within a price range."""

   @tool
   async def filter_meals(meals: list[dict], exclude_category: str = None, min_confidence: int = 50) -> list[dict]:
       """Filter a meal list by category exclusion or confidence threshold."""

   @tool
   async def get_meal_insight(meal_id: int) -> str:
       """Get AI value insight for a specific meal."""

   @tool
   async def get_price_trend(meal_id: int) -> str:
       """Get price trend for a meal: rising, falling, or stable."""

   @tool
   async def semantic_search_meals(query: str, limit: int = 10) -> list[dict]:
       """Semantic search for meals by description or cuisine type."""
   ```
2. Build `ai/graphs/assistant_graph.py` — LangGraph ReAct agent:
   ```python
   from langgraph.prebuilt import create_react_agent
   assistant = create_react_agent(
       model=ChatGroq(model="llama-3.3-70b-versatile"),
       tools=[search_nearby_meals, filter_meals, get_meal_insight, get_price_trend, semantic_search_meals],
       checkpointer=checkpointer,   # enables conversation memory
   )
   ```
3. `POST /api/v1/chat` endpoint — SSE streaming:
   - Body: `{ "message": "...", "lat": ..., "lng": ..., "thread_id": "..." }`
   - Stream `agent.astream_events()` → SSE events: `{ type: "thinking" | "tool_call" | "tool_result" | "response" }`
4. Frontend: chat panel in homepage sidebar. Shows agent "thinking" state + tool calls in real time.
5. System prompt: include user location, budget preference, and conversation history.

**Output:** Conversational food assistant with tool use. SSE streaming. Multi-turn memory via checkpointer.

**DoD:**
- "find biryani under 200 near NUST" → agent calls `search_nearby_meals` + `filter_meals` → returns ranked results
- Agent refuses off-topic queries ("what is the capital of France?") — system prompt enforces scope
- Follow-up question "what about karahi?" uses context from previous turn (checkpointer)
- Tool calls visible in SSE stream on frontend

---

### DAY 15 — Personalized Feed (LangChain + pgvector)

**Prerequisites:**
- User must have saved meals or report history for personalization. Seed test users with saves in `scripts/seed_islamabad.py`.

**KPI:**
- `/api/v1/feed` returns personalized meal list for authenticated users. Anonymous users get popularity-based ranking. Relevance score > generic `/nearby` for users with history.

**Tasks:**
1. Create `ai/chains/personalization_chain.py`:
   ```python
   personalization_chain = (
       fetch_user_profile          # saved meal IDs + categories + avg price range
       | build_user_taste_embedding  # average embedding of saved meal embeddings
       | pgvector_personalized_search  # ORDER BY embedding <=> user_taste_vec + Foodly Score blend
       | rerank_with_foodly_score
   )
   ```
2. `build_user_taste_embedding(user_id)`:
   - Fetch embeddings of all saved meals.
   - Compute centroid: `np.mean(embeddings, axis=0)`.
   - This is the user's "taste profile" in vector space.
3. `pgvector_personalized_search` — SQL:
   ```sql
   SELECT *, (embedding <=> :taste_vec) AS taste_distance
   FROM meals
   WHERE ST_DWithin(location, :user_point, :radius)
   ORDER BY (0.6 * foodly_score + 0.4 * (1 - taste_distance)) DESC
   LIMIT 20
   ```
4. `GET /api/v1/feed?lat=&lng=&radius_km=` — authenticated → personalized, anonymous → Foodly Score sort.
5. Add `personalization_score` to feed response items.

**Output:** Personalized feed endpoint. User taste profile via embedding centroid.

**DoD:**
- User with 5 saved biryani meals → feed shows more biryani/desi options than generic `/nearby`
- Anonymous user → falls back to standard Foodly Score sort
- `personalization_score` in response (0–100)

---

### DAY 16 — Nightly Enrichment Supervisor Agent (LangGraph Multi-Agent)

**Prerequisites:**
- Understand LangGraph's `Send()` API — it allows fanning out to multiple parallel sub-agent runs with different inputs.
- The price scraper agent (Day 9) becomes a reusable sub-agent invoked by the supervisor.

**KPI:**
- Supervisor agent triggers price scraping for top-50 meals in parallel. All results collected and stored. HTTP server unaffected during the run.

**Tasks:**
1. Create `ai/graphs/supervisor_graph.py`:
   ```python
   class SupervisorState(TypedDict):
       meals_to_process: list[dict]      # [{meal_id, name, category}]
       completed: list[dict]             # results from sub-agents
       failed: list[int]                 # meal IDs that failed
       run_id: str

   def distribute_node(state: SupervisorState):
       # Fan out: one Send() per meal → runs price_agent sub-graph in parallel
       return [Send("scrape_meal", {"meal_id": m["meal_id"], "search_query": f"{m['name']} price Islamabad"})
               for m in state["meals_to_process"]]

   def aggregate_node(state: SupervisorState):
       # Collect all sub-agent results, insert to pending_verifications in batch
       ...
   ```
2. Wire supervisor: `SELECT_TOP_50 → distribute_node (fan-out via Send) → [price_agent × 50] → aggregate_node → REPORT → END`.
3. APScheduler cron at 2am PKT: fetch top-50 meals by `report_count DESC`, invoke supervisor.
4. `POST /api/v1/admin/agent/run-enrichment` — manual trigger endpoint (admin only).
5. `GET /api/v1/admin/agent/enrichment-status` — current run progress from supervisor state.

**Output:** Multi-agent supervisor. Parallel scraping fan-out. Nightly enrichment schedule.

**DoD:**
- Trigger enrichment → LangGraph logs show 50 parallel sub-agent runs
- All results in `pending_verifications` within 60 seconds
- HTTP server p95 latency unaffected during enrichment run (verify with concurrent k6 test)
- `GET /admin/agent/enrichment-status` shows `{ completed: 47, failed: 3, in_progress: 0 }`

---

### DAY 17 — LangSmith Integration + AI Observability

**Prerequisites:**
- You cannot improve AI quality without observability. LangSmith traces every LangGraph/LangChain call: inputs, outputs, latency, token count, cost.

**KPI:**
- Every AI call (insight chain, price agent, assistant, expansion chain, validator) traced in LangSmith. Token cost per endpoint tracked. Slow chains identified.

**Tasks:**
1. Add LangSmith to `core/config.py`:
   ```python
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=...
   LANGCHAIN_PROJECT="foodly-production"
   ```
2. Tag all chains and graphs with metadata:
   ```python
   config = {"metadata": {"meal_id": meal_id, "user_id": user_id, "endpoint": "/meals/{id}/insight"}}
   await insight_chain.ainvoke(context, config=config)
   ```
3. Create LangSmith datasets for evaluation:
   - `insight_eval_set`: 20 meal contexts → expected verdict (ground truth from manual review)
   - `search_eval_set`: 15 queries → expected top-3 meals
4. LangSmith evaluators:
   - Insight: `verdict_accuracy` — does chain return the correct verdict?
   - Search: `recall@5` — are expected meals in top-5 results?
5. Run evaluations: `langsmith_client.run_on_dataset(dataset_name, chain)`. Document scores in `docs/ai_eval.md`.
6. Add token cost tracking: log `prompt_tokens`, `completion_tokens`, `cost_usd` per endpoint in structured logs.

**Output:** LangSmith tracing for all AI calls. Eval datasets. Token cost tracking.

**DoD:**
- LangSmith dashboard shows traces for `insight_chain`, `assistant`, `price_agent`, `expansion_chain`
- Each trace has `meal_id` and `user_id` in metadata (for debugging)
- `insight_eval_set` run: `verdict_accuracy` ≥ 75%
- Token cost per `/meals/{id}/insight` call logged and visible in structured logs

---

### DAY 18 — AI Streaming Responses (Gemini SSE + Frontend)

**Prerequisites:**
- Currently all AI calls are blocking: `llm.invoke()` waits for the full response. For insight (1–2s) and chat (2–4s), streaming dramatically improves perceived performance.

**KPI:**
- AI insight streams tokens to frontend progressively. Chat assistant streams thoughts and tool calls in real time. Time-to-first-token < 300ms.

**Tasks:**
1. Insight streaming endpoint `GET /api/v1/meals/{id}/insight/stream` (SSE):
   ```python
   async def event_generator():
       async for chunk in insight_chain.astream(context):
           yield {"event": "token", "data": chunk.content}
       yield {"event": "done", "data": json.dumps({"verdict": ..., "price_percentile": ...})}
   return EventSourceResponse(event_generator())
   ```
2. Replace `agent.py:event_generator` (existing SSE for price scraper) — align event format:
   - `{ event: "thinking", data: "Searching Tavily..." }`
   - `{ event: "tool_call", data: { tool: "search_nearby_meals", args: {...} } }`
   - `{ event: "tool_result", data: [...meals] }`
   - `{ event: "token", data: "Based on..." }` (streaming tokens)
   - `{ event: "done", data: { final_response } }`
3. Frontend: `hooks/useSSE.ts` — handle progressive token rendering for insight card. Chat panel already wired from Day 14 — just align event types.
4. Cache only the final complete insight (not streaming chunks) in Redis.

**Output:** Streaming insight endpoint. Aligned SSE event format across all AI endpoints. Time-to-first-token < 300ms.

**DoD:**
- `/meals/{id}/insight/stream` — first SSE event arrives < 300ms after request
- Tokens render progressively in the insight card (not blank → sudden full text)
- Disconnecting browser mid-stream → generator stops (check `request.is_disconnected()`)
- Event format consistent: `insight/stream`, `live-price`, `/chat` all use same event type schema

---

### DAY 19 — AI Error Handling + Fallback Strategy Audit

**Prerequisites:**
- Production AI calls fail. Gemini rate-limits. Tavily times out. Groq returns empty output. Every AI call needs a defined fallback.

**KPI:**
- Every AI endpoint returns a meaningful degraded response (not 500) when the underlying model fails. Error rate for AI endpoints < 0.5%.

**Tasks:**
1. Audit every AI call path — document failure modes:
   | Endpoint | AI Call | Failure | Fallback |
   |----------|---------|---------|---------|
   | `GET /meals/{id}` | insight_chain | Gemini timeout | Return `{ verdict: "unavailable", summary: "..." }` |
   | `GET /meals/search` | embed_query | Gemini API down | Fall back to ILIKE |
   | `POST /chat` | assistant | Groq error | `"I'm having trouble connecting. Try again shortly."` |
   | `GET /live-price` | price_agent | Tavily quota | Return `{ status: "unavailable" }` |
   | `POST /reports` | validation_chain | Groq error | Skip validation, insert as `needs_review` |
2. Implement `ai/core/safe_invoke.py`:
   ```python
   async def safe_invoke(chain, input, fallback, timeout_s=10):
       try:
           return await asyncio.wait_for(chain.ainvoke(input), timeout=timeout_s)
       except asyncio.TimeoutError:
           logger.warning("AI call timed out", chain=chain.__class__.__name__)
           return fallback
       except Exception as e:
           logger.error("AI call failed", error=str(e))
           return fallback
   ```
3. Replace all raw `chain.ainvoke()` calls with `safe_invoke(chain, input, fallback=...)`.
4. Add circuit breaker for Gemini: if 5 consecutive failures, skip AI for 60s (don't hammer a failing API).
5. Test all fallback paths: temporarily set wrong API keys, verify degraded responses.

**Output:** `safe_invoke` wrapper. Defined fallbacks for all AI paths. Circuit breaker for Gemini.

**DoD:**
- Set `GOOGLE_API_KEY=wrong` → all Gemini calls return fallback, zero 500 errors
- Set `GROQ_API_KEY=wrong` → chat, validator, expansion all return fallbacks
- Tavily quota exhausted → price agent returns `{ status: "unavailable" }` not 500
- Circuit breaker logs: "Gemini circuit open — skipping for 60s"

---

### DAY 20 — Layer 2 Checkpoint: AI Evaluation + Integration Tests

**KPI:**
- All AI workflows tested end-to-end. LangSmith eval scores meet targets. No fake data anywhere in codebase.

**Tasks:**
1. AI integration tests `tests/ai/`:
   - `test_insight_chain.py` — 5 meals → assert `verdict` is valid enum, `price_percentile` is 0–100
   - `test_price_agent.py` — trigger agent → assert row appears in `pending_verifications`
   - `test_assistant.py` — 3 user queries → assert tool calls made, response is food-related
   - `test_query_expansion.py` — "desi food" → assert ≥ 3 expanded terms returned
   - `test_report_validator.py` — PKR 5 for biryani → assert auto-rejected
   - `test_hitl.py` — agent pauses → admin resumes → price updated
2. Run LangSmith eval datasets. Targets:
   - Insight `verdict_accuracy` ≥ 75%
   - Search `recall@5` ≥ 80%
3. Final fake data audit — `grep -r "random.uniform\|random.randint\|mock\|fake" backend/app/` — must return zero matches.
4. Document all AI workflows in `docs/ai_architecture.md` — one ASCII diagram per workflow.

**Output:** Full AI test suite. LangSmith eval scores. Zero fake data.

**DoD:**
- `pytest tests/ai/` — 0 failures
- LangSmith dashboard: insight `verdict_accuracy` ≥ 75%, search `recall@5` ≥ 80%
- `grep -r "random.uniform" backend/app/` returns 0 matches
- `docs/ai_architecture.md` committed with diagrams for all 6 AI workflows

---

## LAYER 3 — PERFORMANCE LAYER (Days 21–26)

### DAY 21 — Query Optimization + Indexing

**Prerequisites:** Run `EXPLAIN (ANALYZE, BUFFERS)` on the 5 slowest endpoints. Never optimize without measuring first.

**KPI:** Zero sequential scans on tables > 100 rows. `/nearby` p95 < 200ms without cache.

**Tasks:**
1. Run `EXPLAIN (ANALYZE, BUFFERS)` on: `/nearby`, `/search`, `/feed`, `/admin/reports`, `saved_meals` query.
2. Add missing indexes based on query plans:
   - `meals(restaurant_id)`, `meals(category, price)`, `price_reports(meal_id, status)`, `saved_meals(user_id)`, `pending_verifications(status, created_at)`.
3. Move Foodly Score sort to SQL expression — avoid Python loops over result sets.
4. Add `LIMIT` enforcement in all repositories — no unbounded queries.
5. Re-run `EXPLAIN ANALYZE` after changes. Document before/after in `docs/benchmarks.md`.

**Output:** Optimized query plans. All indexes documented.

**DoD:**
- Zero `Seq Scan` on any production query against tables > 100 rows
- `/nearby` p95 < 200ms measured with `wrk`

---

### DAY 22 — Redis Caching Layer

**Prerequisites:** Measure uncached latencies first (Day 21). Cache what is proven slow.

**KPI:** Cache hit rate > 60% on search. Cached response latency < 50ms.

**Tasks:**
1. `core/cache.py`: `get_cached`, `set_cached`, `invalidate_pattern`.
2. Cache with TTLs: `search:{hash}` → 15 min, `nearby:{hash}` → 5 min, `insight:{meal_id}` → 24 hr, `feed:{user_id}:{hash}` → 10 min.
3. Cache invalidation on writes: price change → invalidate `insight:{meal_id}`, `nearby:*`, `feed:*`.
4. `X-Cache: HIT | MISS` header on all cached responses.
5. Redis health check in `GET /health`.

**Output:** Redis caching on all hot paths. Cache-aware invalidation.

**DoD:**
- Two identical `/search?q=biryani` → first `MISS`, second `HIT`
- Cached response latency < 50ms
- Price change invalidates correct insight cache key

---

### DAY 23 — Rate Limiting + OWASP Security Hardening

**KPI:** Rate limiting per IP and per user. OWASP Top 10 passed for all endpoints.

**Tasks:**
1. `slowapi` rate limits: global 100/min per IP, `/auth/login` 5/min per IP, `/search` 30/min per user, `/reports` 10/min per user. `429` with `Retry-After` header.
2. SQL injection audit: all repositories use SQLAlchemy ORM or parameterized `text()`. Test: `'; DROP TABLE meals; --` in search → safe.
3. XSS: `bleach.clean()` on all string inputs before storage.
4. Security headers middleware: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`.
5. AI-specific rate limits: `/chat` 10/min per user (expensive), `/live-price` 5/min per user.

**Output:** Rate-limited API. Security headers. SQL-injection–safe codebase.

**DoD:**
- 6th login attempt in 1 min from same IP → `429`
- SQL injection string in search → empty results, not 500
- `curl -I localhost/api/v1/meals` shows all 5 security headers
- `/chat` — 11th request in 1 min → `429`

---

### DAY 24 — AI Response Caching Strategy

**Prerequisites:** AI calls are expensive (tokens cost money). Cache aggressively but invalidate correctly.

**KPI:** Token cost per 1,000 requests reduced by ≥ 50% via caching. Cache hit rate for insights ≥ 80%.

**Tasks:**
1. Semantic cache for chat assistant — similar queries return cached responses:
   - Hash query embedding → `chat:{embedding_hash}` → if similar cached response exists (cosine distance < 0.1), return it.
   - Use Redis + pgvector for semantic cache lookup.
2. Cache insight chain by `meal_id` + `price` (if price changes, insight is stale):
   - Key: `insight:{meal_id}:{price_cents}` — automatically invalidated when price changes.
3. Cache expansion chain results: `expansion:{query_hash}` → 1 hour TTL.
4. Cache validation chain results: `validation:{meal_id}:{reported_price}` → 6 hours (prices don't change that fast).
5. Log token savings: before/after token counts with semantic cache enabled.

**Output:** Semantic cache for chat. Price-aware insight cache. Token cost reduced.

**DoD:**
- Same question asked twice in chat → second call served from semantic cache (no Groq call)
- Meal price changes → insight cache with old price invalidated, new key used
- Token cost per 100 `/insight` requests reduced by ≥ 50% (compare LangSmith token counts)

---

### DAY 25 — Layer 3 Benchmark + Performance Audit

**KPI:** All p95 latency targets met. Cache hit rates measured. OWASP ZAP baseline scan passes.

**Tasks:**
1. `k6` load test: 50 VUs × 60s on `/nearby`, `/search`, `/feed`, `/chat` (5 VUs for expensive AI endpoint).
2. Record: p50, p95, p99, req/s, error rate.
3. Redis cache hit rates: `redis-cli INFO stats`.
4. OWASP ZAP baseline scan → fix any HIGH severity findings.
5. Update `docs/benchmarks.md` with Layer 3 results.

**Output:** Benchmark report. OWASP baseline passed.

**DoD:**
- `/nearby` p95 < 150ms (cached), < 250ms (cache miss)
- `/search` p95 < 100ms (cached)
- `/chat` p95 < 3s (AI call — acceptable)
- Zero HIGH severity in OWASP ZAP baseline

---

### DAY 26 — Full Test Suite + Layer 3 Cleanup

**KPI:** `pytest` 100% pass rate. No dead code. No open `TODO`s in critical paths.

**Tasks:**
1. Run full `pytest` suite — fix all failures.
2. Audit: remove all `print()` statements — replace with `structlog` calls.
3. Remove unused imports, dead code, commented-out blocks.
4. All environment variables documented in `.env.example`.

**Output:** Clean, fully-tested codebase. Production-ready Layer 3.

**DoD:**
- `pytest` 100% pass
- `grep -r "print(" backend/app/` returns 0 (only `backend/ai/` scripts allowed)
- `.env.example` has every variable used in `config.py`

---

## LAYER 4 — REAL-TIME LAYER (Days 27–31)

### DAY 27 — WebSocket Server + Connection Manager

**Prerequisites:** REST polling at scale is wasteful. 500 users × 5s poll = 6,000 req/min for nothing. WebSockets eliminate this.

**KPI:** Authenticated WebSocket connections live. Heartbeat working. Auto-reconnect on frontend.

**Tasks:**
1. `core/websocket_manager.py` — `ConnectionManager`:
   ```python
   class ConnectionManager:
       active: dict[int, list[WebSocket]]  # user_id → connections
       async def connect(ws, user_id)
       async def disconnect(ws, user_id)
       async def send_to_user(user_id, message: dict)
       async def broadcast(message: dict)
       async def send_to_admins(message: dict)
   ```
2. `ws://host/api/v1/ws?token=JWT` — authenticate on connect. Close `4001` if invalid.
3. Heartbeat: server pings every 30s, client must pong within 10s or disconnect.
4. `hooks/useWebSocket.ts` — auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s).
5. Redis tracks online user count: `INCR/DECR foodly:online_users` on connect/disconnect.

**Output:** WebSocket server. Authenticated connections. Auto-reconnecting frontend hook.

**DoD:**
- Invalid JWT → closed `4001` immediately
- Two tabs from same user both receive messages
- Disconnect tab → `ConnectionManager` removes it within 5s (heartbeat timeout)

---

### DAY 28 — Live Price Updates + Report Notifications

**KPI:** Admin approves report → reporter browser shows notification < 200ms. No page refresh.

**Tasks:**
1. `ReportService.approve()` → `await manager.send_to_user(reporter_id, { type: "report_approved", meal_id, new_price })`.
2. On price change → query `saved_meals` → `send_to_user` for all users who saved that meal: `{ type: "price_changed", meal_id, old_price, new_price }`.
3. New report submitted → `send_to_admins({ type: "new_report", meal_id, reported_price })`.
4. AI agent pauses at HITL interrupt → `send_to_admins({ type: "agent_needs_review", thread_id, meal_id, extracted_price })`.
5. Frontend: toast notifications for `report_approved`, `price_changed`. Admin live feed for `new_report` and `agent_needs_review`.

**Output:** Real-time notifications. Admin live feed. Agent HITL events via WebSocket.

**DoD:**
- Admin approves report → reporter toast appears < 200ms (no refresh)
- New price report submitted → admin pending count increments live
- Agent pauses at HITL → admin sees `agent_needs_review` notification live

---

### DAY 29 — AI Agent Events via WebSocket

**KPI:** Chat assistant streams reasoning and tool calls to frontend via WebSocket (not just SSE). Agent status visible in real time.

**Tasks:**
1. Move chat assistant from SSE (`/chat` GET) to WebSocket message type `chat_message`:
   - Client sends: `{ type: "chat_message", message: "find biryani near NUST", thread_id: "..." }`
   - Server streams back: `{ type: "thinking" }`, `{ type: "tool_call", tool: "..." }`, `{ type: "token", text: "..." }`, `{ type: "done", result: {...} }`
2. Price agent job status via WebSocket:
   - `{ type: "agent_started", job_id, meal_id }`
   - `{ type: "agent_searching", job_id }`
   - `{ type: "agent_found", job_id, price, confidence }`
   - `{ type: "agent_done", job_id }`
3. Frontend chat panel: uses WebSocket (not SSE). Renders streaming tokens and tool call badges.

**Output:** WebSocket-native chat assistant. Agent job status events.

**DoD:**
- Chat message → tool call badges appear live on frontend, then tokens stream in
- Price agent triggered → status updates arrive via WebSocket without polling
- Same WebSocket connection handles chat + notifications + agent events (multiplexed by `type`)

---

### DAY 30 — Live Search Suggestions + Online Presence

**KPI:** Search suggestions appear < 400ms after keypress. Online user count live in admin.

**Tasks:**
1. Client sends `{ type: "search_suggest", query: "bir" }` (debounced 300ms) via WebSocket.
2. Server: embed query → vector similarity → top 5 meal name suggestions. Redis cache: `suggest:{hash}` → 5 min TTL.
3. Online user count: `GET /admin/stats` includes `online_users` from Redis. Admin panel updates every 10s via WebSocket broadcast.

**Output:** Live search suggestions. Online presence tracking.

**DoD:**
- Type "bir" → suggestions appear < 400ms
- Online count changes when new tab connects/disconnects

---

### DAY 31 — WebSocket Load Test + Layer 4 Checkpoint

**KPI:** 200 concurrent WS connections stable. No memory leaks. All Layer 4 tests pass.

**Tasks:**
1. k6 WebSocket load test: 200 connections × 60s × 1 msg/5s. Measure: connection success rate, message delivery rate, memory.
2. Fix any memory leaks in `ConnectionManager` (connections not removed on error).
3. Test reconnection: kill server → verify all clients reconnect within 30s.
4. `pytest tests/integration/test_websocket.py` — all pass.

**Output:** Load-tested WebSocket layer. Memory-leak-free ConnectionManager.

**DoD:**
- 200 concurrent WS: 0 dropped messages, stable memory over 60s
- Server restart → all clients reconnected within 30s

---

## LAYER 5 — EVENT-DRIVEN LAYER (Days 32–38)

### DAY 32 — Kafka Setup + Topics

**Prerequisites:**
- Understand why Kafka over Redis Pub/Sub for this use case: Kafka events are durable (survive consumer downtime), ordered (price changes happen in sequence), and replayable (audit trail). Redis Pub/Sub is fire-and-forget.
- Kafka is introduced only now because the monolith works. Add complexity only when the sync approach has a proven problem (HTTP response blocked by side effects).

**KPI:** Kafka running via Docker Compose. All topics created. Round-trip verified.

**Tasks:**
1. `docker-compose.yml` — add `zookeeper` + `kafka` (Confluent 7.5.0) + `kafka-ui`.
2. Topics: `report.approved`, `report.rejected`, `meal.price_changed`, `scrape.job_requested`, `scrape.job_completed`, `agent.hitl_decision`, `chat.session_ended`.
3. `core/kafka_producer.py`: `async def emit(topic, key, value: dict)`.
4. Kafka health check in `GET /health`.
5. Produce 100 messages → consume all 100 → verify order.

**Output:** Kafka running. All topics created. Producer utility.

**DoD:**
- `GET /health` → `{ "kafka": "connected" }`
- Topics visible in kafka-ui at `localhost:8080`
- 100-message round-trip: 0 loss, correct order

---

### DAY 33 — Decouple HTTP Handlers via Events

**KPI:** Report approval HTTP response < 50ms. All side effects moved to consumers.

**Tasks:**
1. `ReportService.approve()` — emit `report.approved` event. Remove all sync side effects (WS push, cache invalidation, email).
2. Similarly for `reject()` → `report.rejected`, price change → `meal.price_changed`, agent trigger → `scrape.job_requested`, HITL decision → `agent.hitl_decision`.
3. Measure before/after: `time curl -X PATCH .../reports/1/approve`.

**Output:** Decoupled HTTP handlers. All side effects are async events.

**DoD:**
- `PATCH /admin/reports/{id}/approve` response time < 50ms
- No WebSocket calls, cache invalidations, or email sends inside HTTP handlers

---

### DAY 34 — Event Consumers (Workers)

**KPI:** Three workers consuming events. All side effects triggered correctly by events.

**Tasks:**
1. `workers/notification_worker.py` — consumes `report.approved`, `report.rejected`, `meal.price_changed` → pushes WebSocket notifications.
2. `workers/cache_worker.py` — consumes same topics → invalidates Redis keys.
3. `workers/email_worker.py` — consumes `report.approved` → sends Resend email.
4. Each worker as a separate `docker-compose.yml` service.
5. Consumer lag alert: log warning if lag > 100 messages.

**Output:** Three async event consumers.

**DoD:**
- Approve report → WS notification, cache invalidated, email sent — all within 2s
- Stop `notification_worker` → restart → queued events processed (Kafka durability verified)

---

### DAY 35 — AI Agent Pipeline via Kafka

**KPI:** Nightly scraping triggered via Kafka. HTTP server unaffected. Scraper worker processes events.

**Tasks:**
1. `workers/scraper_worker.py` — consumes `scrape.job_requested` → runs LangGraph price agent → emits `scrape.job_completed`.
2. `workers/verification_worker.py` — consumes `scrape.job_completed` → inserts to `pending_verifications` → WS push to admins.
3. `workers/hitl_worker.py` — consumes `agent.hitl_decision` → resumes LangGraph graph via checkpointer.
4. APScheduler cron 2am PKT: fetch top-50 meals → emit 50 `scrape.job_requested` events.
5. HTTP server p95 unaffected during nightly run (verify with concurrent k6).

**Output:** Fully async AI pipeline. Workers for scraping, verification, HITL resume.

**DoD:**
- Trigger enrichment → 50 events in Kafka → scraper_worker processes all → results in `pending_verifications`
- HTTP p95 unaffected during scraping run
- HITL decision event → graph resumes correctly via `hitl_worker`

---

### DAY 36 — Correlation IDs + Dead-Letter Queues

**KPI:** Every event traceable end-to-end by `correlation_id`. Failed events go to DLQ.

**Tasks:**
1. Add `correlation_id: uuid4()` to every event payload. Log it in every consumer log line.
2. DLQ: `{topic}.dlq` topic. If consumer fails 3 times, send to DLQ and alert.
3. `tests/integration/test_event_pipeline.py` — emit event → assert consumer processed → assert side effect occurred.
4. Document event topology in `docs/event_topology.md` (ASCII diagram).

**Output:** Traceable events. Dead-letter queues. Event pipeline tests.

**DoD:**
- Every log line for event-driven action has `correlation_id`
- DLQ receives event when consumer throws 3 times
- `pytest tests/integration/test_event_pipeline.py` passes

---

### DAY 37 — Layer 5 Checkpoint + Full Stack Test

**KPI:** All 5 layers working together. End-to-end flow tested with events, WebSockets, and AI.

**Tasks:**
1. End-to-end test: user sends chat message → AI assistant calls tools → results returned via WebSocket → user saves a meal → price report submitted → AI validates → admin approves via HITL → Kafka event emitted → WS notification received.
2. All consumers running and healthy (`docker-compose ps`).
3. Kafka consumer lag < 10 for all topics (steady state).
4. Full `pytest` suite passes.

**Output:** Full-stack integration verified.

**DoD:**
- End-to-end test passes without manual intervention
- All consumer lags < 10
- `pytest` 100% pass

---

### DAY 38 — Performance Audit Post-Event Layer

**KPI:** Adding Kafka+workers hasn't degraded HTTP performance. Workers not overloaded.

**Tasks:**
1. k6 load test with all workers running: 100 VUs × 120s.
2. Monitor: Kafka consumer lag, worker CPU, Redis memory, DB connection pool.
3. Fix any bottlenecks found.
4. Document Layer 5 benchmarks.

**Output:** Performance validated with full event-driven stack.

**DoD:**
- HTTP p95 same as Layer 3 benchmarks (no regression)
- Consumer lag stays < 10 under load
- Worker CPU < 70%

---

## LAYER 6 — PRODUCTION LAYER (Days 39–50)

### DAY 39 — Docker + Docker Compose (Full Stack)

**KPI:** Entire stack starts with `docker-compose up --build`. Zero manual steps.

**Tasks:**
1. `backend/Dockerfile` — multi-stage: `builder` (pip install) → `runtime` (copy app only). Target < 200MB.
2. `frontend/Dockerfile` — 3-stage: `deps` → `builder` → Next.js standalone runner.
3. `docker-compose.yml` — all services: `postgres`, `redis`, `zookeeper`, `kafka`, `backend`, 4 workers, `frontend`.
4. `docker-compose.override.yml` — dev: volume-mount source, hot reload.
5. `docker-compose.prod.yml` — prod: no volumes, resource limits, health checks.
6. Verify: all services `Up (healthy)` within 60s.

**Output:** Full Docker Compose stack. Dev/prod config separation.

**DoD:**
- `docker-compose up --build` → all services healthy
- Backend image < 200MB
- `docker-compose down && up` → data persists (Postgres volume)

---

### DAY 40 — CI/CD Pipeline (GitHub Actions)

**KPI:** PR merge blocked if tests fail. Push to `main` → image on ECR within 5 minutes.

**Tasks:**
1. `.github/workflows/ci.yml` — on PR/push: start services, run migrations, `pytest --cov=app`, `ruff`, `mypy`, `eslint`. Fail if coverage < 70%.
2. `.github/workflows/deploy.yml` — on `main`: build image → push ECR → deploy ECS → run migrations.
3. Branch protection: require CI to pass before merge.
4. Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`.

**Output:** Automated CI/CD. Protected main branch.

**DoD:**
- PR with failing test → CI fails → merge blocked
- Merge to main → ECR image updated within 5 min
- No secrets in any `.yml` file

---

### DAY 41 — AWS Infrastructure

**KPI:** FastAPI live on ECS Fargate. PostgreSQL on RDS. Redis on ElastiCache. HTTPS working.

**Tasks:**
1. VPC with public + private subnets.
2. RDS PostgreSQL 15 (private subnet, `db.t3.micro`, PostGIS + pgvector enabled, 7-day backup).
3. ElastiCache Redis (`cache.t3.micro`, private subnet).
4. ECS Fargate: backend service + 4 worker services.
5. ALB with HTTPS termination (ACM cert for `api.foodly.pk`).
6. AWS Secrets Manager: all API keys and DB credentials.
7. Route 53: `api.foodly.pk` → ALB. Frontend on Vercel: `foodly.pk`.
8. **AI-specific:** ensure ECS task role has Secrets Manager access for all AI API keys.

**Output:** Production AWS infrastructure. HTTPS API live.

**DoD:**
- `https://api.foodly.pk/health` → `{ "status": "ok" }` with valid SSL
- `https://foodly.pk` loads from Vercel
- All AI API keys via Secrets Manager (not in task definition)

---

### DAY 42 — Structured Logging + Metrics

**KPI:** Structured JSON logs in CloudWatch. Prometheus metrics live. LangSmith wired to production.

**Tasks:**
1. `structlog` — every log line: `{ timestamp, level, service, correlation_id, endpoint, latency_ms, status_code, user_id }`.
2. `prometheus-fastapi-instrumentator` — metrics: `http_request_duration_seconds`, `active_websocket_connections`, `kafka_consumer_lag`, `ai_call_duration_seconds` (per chain/graph).
3. CloudWatch dashboards: p95 per endpoint, error rate, active WS connections, Kafka lag, AI call latency.
4. Alerts: p95 > 500ms for 5min → email. Error rate > 1% → email. RDS CPU > 80% → email.
5. Sentry: `sentry-sdk` with `traces_sample_rate=0.1`.
6. LangSmith production project: `LANGCHAIN_PROJECT=foodly-production`.

**Output:** Full observability. AI-specific metrics. Alerts configured.

**DoD:**
- Trigger 500 error → Sentry shows stack trace within 30s
- CloudWatch dashboard shows AI call latency per chain
- Alert fires at > 1% error rate (test by temporarily breaking an endpoint)

---

### DAY 43 — Load Testing Production

**KPI:** 200 concurrent users at p95 < 200ms. AI endpoints stable under load.

**Tasks:**
1. k6 load test against staging (200 VUs, ramp 2min, hold 5min, ramp down 2min). Thresholds: p95 < 200ms, error rate < 1%.
2. Separate test for AI endpoints (20 VUs — expensive): `/chat`, `/insight`, `/live-price`.
3. AI endpoint thresholds: `/insight` p95 < 3s, `/chat` p95 < 5s (streaming, so time-to-first-token < 300ms).
4. DB connection pool tuning: `pool_size=20, max_overflow=10`.
5. Fix bottlenecks found. Re-run.

**Output:** Load test report. Tuned connection pool.

**DoD:**
- k6 report: p95 < 200ms at 200 VUs, error rate < 1%
- `/insight` time-to-first-token < 300ms
- DB connections during test < 30 (pool not exhausted)

---

### DAY 44 — Security Audit

**KPI:** OWASP ZAP active scan: 0 HIGH/CRITICAL. No secrets in git history.

**Tasks:**
1. OWASP ZAP active scan against staging. Fix all HIGH/CRITICAL.
2. Manual checklist: JWT expiry enforced, token revocation works, rate limiting active, SQL injection safe, mass assignment blocked.
3. `pip-audit` + `npm audit` — fix HIGH CVEs.
4. `truffleHog --regex .` — no secrets in git history.
5. AI-specific: ensure LangSmith traces don't log PII (user messages, meal queries with user location). Configure `hide_inputs=True` for sensitive chains.
6. ECS security groups: backend only accepts traffic from ALB.

**Output:** Security audit passed. LangSmith PII protection.

**DoD:**
- ZAP active scan: 0 HIGH, 0 CRITICAL
- `truffleHog`: no secrets found
- LangSmith traces: no raw user location data visible in inputs
- `pip-audit`: 0 HIGH CVEs

---

### DAY 45 — AI Cost Optimization + Token Budget

**KPI:** Monthly AI API cost projected ≤ $50 at 1,000 MAU. Token budget enforced per request.

**Tasks:**
1. Audit token usage per endpoint via LangSmith:
   - `/insight`: avg tokens per call
   - `/chat`: avg tokens per message
   - `/live-price`: avg tokens per scrape
   - `/search` (query expansion): avg tokens per search
2. Token budget enforcement:
   - Insight chain: max 2,000 output tokens (insight is 2 sentences, not an essay)
   - Chat assistant: max 500 output tokens per turn
   - Query expansion: max 100 output tokens (just a list)
   - Validator: max 200 output tokens
3. Model routing — use cheap model for simple tasks:
   - Query expansion → Groq `llama-3.3-70b` (fast, cheap)
   - Report validation → Groq `llama-3.3-70b` (simple classification)
   - Insight → Gemini `gemini-2.0-flash` (needs reasoning + market context)
   - Chat assistant → Groq `llama-3.3-70b` (latency-sensitive)
4. Projected cost calculation: `(daily_searches × expansion_tokens × cost_per_token) × 30`. Document in `docs/cost_model.md`.

**Output:** Token budgets enforced. Model routing optimized. Cost model documented.

**DoD:**
- Insight response is ≤ 2,000 tokens
- `/chat` single turn is ≤ 500 tokens
- `docs/cost_model.md` shows projected monthly cost ≤ $50 at 1,000 MAU

---

### DAY 46 — Final Integration Test + Demo Flow

**KPI:** Full demo flow works flawlessly in production. All 60-day KPIs verified.

**Tasks:**
1. End-to-end smoke test in production: register → login → search "biryani F-7" (semantic + expansion) → chat "find something cheap near NUST" → get personalized feed → save meal → submit price report → AI validator approves → admin sees HITL notification → resumes graph → price updated → WS notification → AI insight loads (RAG-grounded) → bookmark on profile.
2. `pytest` 100% pass.
3. Verify all 60-day KPIs.
4. Record 3-minute demo video.
5. `ARCHITECTURE.md` with full system diagram including all AI workflows.

**Output:** Production-grade investor-ready Foodly. Full documentation.

**DoD:**
- End-to-end smoke test passes with no errors
- `pytest` 100%
- Demo video recorded
- All 60-day KPIs in table below are green

---

## LAYER 7 — GROWTH & INVESTOR PREP (Days 47–60)

### DAYS 47–48 — Analytics Integration

**Tasks:**
1. Vercel Analytics + Mixpanel: track search queries, meal views, saves, report submissions, chat sessions.
2. AI-specific tracking: insight views, chat messages per session, price agent triggers.
3. Admin analytics dashboard: top searches, top meals, report conversion funnel.
4. Funnel: visit → search → meal detail → save/report → return visit.

**Output:** Full analytics stack. AI usage metrics tracked.

---

### DAYS 49–50 — Monetization Features

**Tasks:**
1. `is_featured` flag on meals — featured meals pinned to top of results with badge.
2. `POST /api/v1/admin/meals/{id}/feature` — admin endpoint to toggle featured status.
3. Restaurant self-service form (Tally embed) → submission → admin reviews → toggles featured.
4. Premium plan stub: `users.plan` column (`free | premium`). Premium users: no rate limits on `/chat`, advanced radius filter, price alerts.
5. Price alert system: user sets `alert_price` on a saved meal. On price drop below threshold → email via Resend.

**Output:** Featured listings. Premium plan structure. Price alerts.

---

### DAYS 51–53 — Viral Features

**Tasks:**
1. Shareable meal cards: `GET /api/v1/meals/{id}/og-image` → generate OG image with meal name, price, Foodly Score (use `satori` or Cloudinary).
2. Reporter leaderboard: `GET /api/v1/leaderboard` — top 10 reporters by `karma_score`.
3. "Meal of the Day": algorithmic pick (`highest foodly_score + recent report + featured = false`) promoted in hero section.
4. AI-powered meal description generation: for meals with empty `description`, run `description_chain` (Groq, cheap) → fill in automatically via nightly cron.

**Output:** Shareable cards. Leaderboard. Meal of the Day. AI-generated descriptions.

---

### DAYS 54–55 — A/B Testing + User Feedback

**Tasks:**
1. GrowthBook: A/B test — control: vector search only, variant: vector + query expansion. Measure click-through-to-detail rate.
2. Feedback widget: in-app modal after 5th session. Tally embed.
3. NPS survey email to all registered users via Resend.

**Output:** A/B test running. Feedback collection live.

---

### DAYS 56–57 — Pitch Deck Metrics Dashboard

**Tasks:**
1. Internal metrics page (`/admin/investor-metrics`):
   - MAU, DAU, registered users, total meals, community reports, NPS
   - AI metrics: daily chat sessions, insights served, price verifications completed
   - Revenue: featured restaurants, premium users, MRR
2. All metrics update in real time via Redis counters.
3. Export as PDF for investor meetings.

**Output:** Investor metrics dashboard. PDF export.

---

### DAYS 58–60 — Final Polish + Investor Readiness

**Tasks:**
1. Fix all remaining UX issues found during dogfooding.
2. Write `README.md` with architecture overview, AI features, and local setup instructions.
3. Prepare data room: architecture diagram, AI workflow diagrams, cost model, load test results, LangSmith eval scores.
4. Rehearse 3-minute demo: search → chat → report → admin HITL → live notification.
5. Write 90-day retrospective: KPIs hit vs missed, what to build next.

**Output:** Investor-ready Foodly. Full documentation. Demo rehearsed.

---

## 60-Day KPI Summary

| KPI | Day 20 (AI Layer) | Day 38 (Event Layer) | Day 60 (Final) |
|-----|-------------------|----------------------|----------------|
| Meals in DB (real data) | ≥ 200 | ≥ 200 | ≥ 500 |
| Fake data (`random.uniform`) | 0 instances | 0 | 0 |
| LangGraph agents live | 2 (price + HITL) | 3 (+supervisor) | 4 (+assistant) |
| LangChain chains live | 3 (insight + expansion + validator) | 3 | 5 (+personalization + description) |
| Insight `verdict_accuracy` (LangSmith) | ≥ 75% | ≥ 75% | ≥ 80% |
| Search `recall@5` | ≥ 80% | ≥ 80% | ≥ 85% |
| `/nearby` p95 (cached) | — | — | < 150ms |
| `/insight` time-to-first-token | < 300ms | < 300ms | < 300ms |
| `/chat` time-to-first-token | < 300ms | < 300ms | < 300ms |
| WS notification latency | — | < 200ms | < 200ms |
| API error rate at 200 VUs | — | — | < 1% |
| HITL workflow end-to-end | ✅ | ✅ | ✅ |
| Token cost (projected @ 1K MAU) | — | — | ≤ $50/month |
| OWASP ZAP HIGH findings | 0 | 0 | 0 |
| `pytest` pass rate | 100% | 100% | 100% |
| LangSmith traces on all AI calls | ✅ | ✅ | ✅ |
| Kafka consumer lag (steady state) | — | < 10 | < 10 |

---

## AI Features Reference

| Feature | Tool | Graph/Chain | Day Built | Status After Day 20 |
|---------|------|------------|-----------|---------------------|
| Semantic search | Gemini embeddings + pgvector | — | Day 5 | ✅ |
| Query expansion | LangChain LCEL + Groq | `expansion_chain` | Day 11 | ✅ |
| Grounded AI insight (RAG) | LangChain LCEL + Gemini | `insight_chain` | Day 10 | ✅ |
| Price scraper with retry + store | LangGraph StateGraph | `price_agent` | Day 9 | ✅ Fixed |
| AI report validator | LangChain LCEL + Groq | `validation_chain` | Day 12 | ✅ |
| Human-in-the-loop verification | LangGraph interrupt + checkpointer | `price_agent` | Day 13 | ✅ |
| Conversational food assistant | LangGraph ReAct + tools | `assistant_graph` | Day 14 | ✅ |
| Personalized feed | LangChain LCEL + pgvector | `personalization_chain` | Day 15 | ✅ |
| Nightly enrichment supervisor | LangGraph multi-agent + Send() | `supervisor_graph` | Day 16 | ✅ |
| AI streaming (SSE) | Gemini/Groq `.astream()` | all chains | Day 18 | ✅ |
| Safe fallbacks / circuit breaker | `safe_invoke` wrapper | all | Day 19 | ✅ |
| AI description generation | LangChain + Groq | `description_chain` | Day 53 | ✅ |
| Semantic response cache | pgvector + Redis | chat cache | Day 24 | ✅ |

---

## Technology Decisions (Justified)

| Decision | Chosen | Why |
|----------|--------|-----|
| LangGraph for price agent | StateGraph with conditional edges | Durable retry logic, HITL interrupt, checkpointing — impossible with plain functions |
| LangGraph for HITL | interrupt() + PostgreSQL checkpointer | Pause/resume across HTTP requests — stateful by design |
| LangGraph for supervisor | Send() fan-out API | True parallel sub-agent execution — not sequential loops |
| LangChain LCEL for chains | `RunnableParallel` + `\|` operator | Parallel context retrieval in one call — insight chain fetches 3 sources simultaneously |
| Groq for fast chains | llama-3.3-70b-versatile | < 500ms inference for expansion, validation, assistant — Gemini is slower |
| Gemini for insight | gemini-2.0-flash | Best reasoning quality for market-grounded analysis — justifies higher latency |
| Tavily for web search | TavilyClient | LLM-optimized snippets — cleaner than raw HTML scraping |
| LangSmith for observability | LangSmith tracing | Native to LangChain/LangGraph — zero extra code for traces |
| pgvector over Pinecone | HNSW index in Postgres | Vectors co-located with relational data — join similarity + price + distance in one SQL query |

---

*Version 5.0 · June 2026 · Next review: Day 20 AI layer checkpoint*

---

## REMEDIATION SPRINT: 7-Day KPI Plan (June 22 – June 28, 2026)
*(Added to address technical debt identified in Architecture Issues Report)*

### Day 1: June 22 — Decoupling the Service Layer
*The goal today is to fix the severe Service Layer violations (Remediation Step 1) to make the codebase testable and maintainable.*
* **KPI:** `api/endpoints/meals.py` contains zero raw database queries or SQLAlchemy `db.query()` calls.
* **Tasks:**
  1. Create `backend/app/repositories/meal.py` and implement the `MealRepository` class (`get_by_id`, `list_paginated`, `vector_search`).
  2. Create `backend/app/services/meal.py` to handle business logic (like computing price history).
  3. Refactor the `meals.py` router to inject the `MealService` rather than a raw `db` session.
* **DoD:** All API endpoints return a `200 OK` and behave identically, but routing logic is completely decoupled from database access.

### Day 2: June 23 — Asynchronous AI Refactoring
*The goal today is to eliminate blocking I/O and thread exhaustion risks (Remediation Step 2).*
* **KPI:** Zero usage of `ThreadPoolExecutor` in the codebase; AI endpoints are 100% natively async.
* **Tasks:**
  1. Refactor `agents.py` (`generate_value_insight`) to become an `async def`.
  2. Replace the synchronous `llm.invoke()` with LangChain's native `await llm.ainvoke()`.
  3. Update the `meals.py` endpoint to properly `await` the insight generator directly in the event loop.
* **DoD:** A load test or simple concurrent script firing 20 requests to the insight endpoint does not block the FastAPI event loop.

### Day 3: June 24 — LangGraph Agent Overhaul
*The goal today is to fix the "fake" LangGraph agent so it actually searches, retries smartly, and writes data (Remediation Step 3).*
* **KPI:** The `price_scraper.py` agent dynamically refines its query on failure and successfully saves results to the database.
* **Tasks:**
  1. Update `should_continue` conditional edge: implement branching for `store`, `retry`, or `end`.
  2. Implement a `retry_node` that uses an LLM to generate a better search query if the previous context yielded low-confidence results.
  3. Implement a `store_node` that writes successful extractions to the `pending_verifications` PostgreSQL table.
* **DoD:** Triggering the agent with a vague query ("food") results in logs showing a refined query, followed by a new row appearing in `pending_verifications`.

### Day 4: June 25 — Smart Query Expansion
*The goal today is to fix the brittleness of the semantic search and improve recall (Remediation Step 5 / Plan Day 11).*
* **KPI:** Searching broad terms like "desi food" returns specific matching meals (e.g., biryani, karahi) via union vector search.
* **Tasks:**
  1. Create `ai/chains/query_expansion_chain.py` using Groq to expand a user's query into 5 related localized terms.
  2. Refactor `SearchService.semantic_search(query)` to run `embed_query` on the original term + all expanded terms in parallel.
  3. Update `MealRepository` to perform a `UNION` semantic search across all embeddings.
* **DoD:** Searching "desi food" returns ≥ 5 relevant Pakistani meals instead of 0. Expansion LLM call completes in < 500ms.

### Day 5: June 26 — Distributed Caching with Redis
*The goal today is to replace the flawed `@lru_cache` memory leaks and prep for horizontal scaling (Remediation Step 4 / Plan Day 22).*
* **KPI:** AI Insights and Search endpoints show a > 60% cache hit rate with a latency of < 50ms on hits.
* **Tasks:**
  1. Spin up a Redis container in your local `docker-compose.yml`.
  2. Remove all `@lru_cache` decorators from `meals.py` and `agents.py`.
  3. Implement `core/cache.py` with asynchronous Redis getters/setters (`get_cached`, `set_cached`).
  4. Implement semantic hashing for search caching and `meal_id` based caching for AI insights (TTL 24 hours).
* **DoD:** Calling the AI insight endpoint twice for the same meal results in the second call bypassing Gemini entirely and returning in < 50ms.

### Day 6: June 27 — Human-in-the-Loop (HITL) Workflow
*The goal today is to connect the database verifications to a durable LangGraph workflow (Plan Day 13).*
* **KPI:** Web agent results pause in a LangGraph state, await manual admin approval, and resume successfully.
* **Tasks:**
  1. Add a PostgreSQL `AsyncPostgresSaver` checkpointer to LangGraph.
  2. Add an `interrupt()` node to the price agent graph (`human_review_node`).
  3. Create the `POST /api/v1/agent/resume/{thread_id}` endpoint for admins to approve/reject.
* **DoD:** Killing and restarting the FastAPI server does not lose the state of a paused LangGraph thread.

### Day 7: June 28 — AI Report Validator Integration
*The goal today is to introduce an LLM gatekeeper to catch spam reports automatically before they reach admins (Plan Day 12).*
* **KPI:** Obvious invalid user-submitted price reports (e.g., PKR 5 for Biryani) are auto-rejected in < 1 second.
* **Tasks:**
  1. Build `ai/chains/report_validation_chain.py` that asks Groq if the reported price is realistic for the given sector.
  2. Implement a statistical fast-path pre-check (if price > 3x sector average, auto-reject without LLM).
  3. Integrate into the `POST /reports` endpoint to append an `ai_validation_score`.
* **DoD:** Submitting a report of PKR 50,000 for chai returns a `422` with an AI-generated rejection reason without creating a database row.
