# Foodly End-to-End Execution Plan

Version 2.0 (May 2026)

## Executive Summary
Foodly is an AI-powered, community-verified budget food discovery platform for Islamabad. The plan below converts the end-to-end vision into a structured, time-boxed execution roadmap with concrete KPIs, phases, and measurable outcomes.

## Program Scope
- Total duration: 90 days / 450 hours
- Daily commitment: 5 hours per day
- Target market: Islamabad / Rawalpindi
- Current stage: MVP complete, scaling phase
- Funding target: PKR 15M / USD 50K seed round
- Phases: Infrastructure → AI → UX → Growth → Monetization → Funding → Scale

## Core Product Promise
Users can discover nearby, affordable meals with live price updates, GPS filtering, and community trust signals. The platform combines semantic search, real-time data enrichment, and verifiable reporting workflows.

## Foodly Score (Core Algorithm)
Every meal receives a 0–100 score calculated in real time:

$$Foodly\ Score = (Budget\ Fit \times 0.40) + (Proximity \times 0.35) + (Confidence \times 0.25)$$

Definitions:
- Budget Fit: higher score when the price is below the user's budget
- Proximity: inversely proportional to distance (0m = 100, 5km = 0)
- Confidence: starts at 100, decays with unverified reports, recovers on verification

## Phase 1: Core Infrastructure (Days 1–15, 75 hours)
Goal: deliver the core promise: accurate geo-filtered search, semantic relevance, and verified community data.

### Day 1 — OpenStreetMap + Real Location Search (5 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | Build a working OpenStreetMap + Leaflet map in Next.js. Render a map panel, allow click-to-select lat/lng, move marker dynamically, and pass coordinates to `/nearby`. Autocomplete is deferred (Nominatim later). | Next.js, OpenStreetMap, Leaflet, React Leaflet | 2 hrs |
| KPI 2 | Add PostGIS + radius filter. Create `/nearby` with `ST_DWithin`, sort by distance. | FastAPI, PostGIS | 2 hrs |
| KPI 3 | Seed 50 real Islamabad restaurants with prices and coordinates. | Python, PostgreSQL | 1 hr |

Revised KPI 1 deliverable:
- Interactive OpenStreetMap map visible in browser
- Marker updates on click
- Coordinates stored in frontend state
- Coordinates ready for backend nearby search

Development philosophy for geolocation:
1. Render map
2. Capture coordinates
3. Show marker
4. Connect backend
5. Add advanced UX later

### Day 2 — pgvector Semantic Search (5 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | Generate embeddings for all meals and store in Vector(1536). | pgvector, Gemini or local model | 2 hrs |
| KPI 2 | Upgrade search to vector similarity with `<=>`, keep ILIKE fallback. | FastAPI, pgvector | 2 hrs |
| KPI 3 | Test 10 Islamabad-specific queries and document results. | Evaluation | 1 hr |

### Day 3 — User Auth + Saved Meals (5 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | JWT register/login, bcrypt password hashing, users table. | FastAPI, python-jose, bcrypt | 2 hrs |
| KPI 2 | Saved meals join table + endpoints + bookmark UI. | Next.js, FastAPI, PostgreSQL | 2 hrs |
| KPI 3 | Minimal profile page with saved meals and report count. | Next.js | 1 hr |

### Days 4–5 — Advanced Data & Performance (10 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | Expand to 200 restaurants across all major sectors and universities. | Python, PostgreSQL | 4 hrs |
| KPI 2 | Redis caching for search (15 min) and AI insights (24 hrs). | Redis, FastAPI, Upstash | 3 hrs |
| KPI 3 | Admin dashboard `/admin` for verifications, reports, stats. | Next.js, FastAPI | 3 hrs |

## Phase 2: AI Engine (Days 16–30, 75 hours)
Goal: live web enrichment, AI-assisted insights, and automated ingestion.

### Days 16–17 — Web Scraping Agent (10 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | LangGraph agent + Google Custom Search + Gemini parsing to JSON. | LangGraph, Google Search API, Gemini | 4 hrs |
| KPI 2 | UI section: “Live from web” results streaming under DB results. | FastAPI streaming, Next.js | 3 hrs |
| KPI 3 | Ingestion pipeline: web results → pending_verifications → approval → meals. | FastAPI, PostgreSQL | 3 hrs |

### Days 18–20 — AI Insights & Foodly Score (15 hours)
| KPI | Task Description | Tech Stack | Time |
| :--- | :--- | :--- | :--- |
| KPI 1 | Upgrade AI insight prompt with neighborhood context and price benchmarks. | Gemini, prompt design | 5 hrs |
| KPI 2 | Implement composite Foodly Score and default sorting. | FastAPI, Python | 5 hrs |
| KPI 3 | Confidence decay + community trust rules refinement. | FastAPI | 5 hrs |

## Technology Stack
Existing stack:
- Frontend: Next.js 14 + Tailwind CSS + Framer Motion
- Backend: FastAPI (Python 3.10+)
- Database: PostgreSQL + pgvector
- AI: LangGraph + Gemini 2.0 Flash

Recommended additions:
- PostGIS for radius filtering
- Google Custom Search API for live web ingestion
- Redis for caching AI insights and search results
- Sentry + Vercel Analytics for monitoring
- React Native + Expo for mobile (Phase 2+)

## Success Criteria
- Core promise: live budget + distance search with verified price data
- AI relevance: semantic search and explainable AI insights
- Trust system: reporting + verification + confidence decay
- Admin ops: actionable dashboard with approval workflow

## Execution Rules
- Time-box each KPI to the stated duration.
- If blocked, ship a mock and move forward.
- Maintain weekly progress logs and KPI completion notes.
