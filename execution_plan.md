# 📊 Foodly: 3-Day Structured Execution Plan (Local Environment)

This plan is optimized for 5 hours of work per day, following the **Vertical Slice (Feature-First)** methodology. All services run locally without Docker.

---

## 📅 DAY 1: The "Budget Explorer" Feature
**Objective**: Build a complete end-to-end search experience.

| KPI | Task Description | Time |
| :--- | :--- | :--- |
| **KPI 1** | Build a premium Search UI in Next.js with a budget slider and a results grid. | 2 Hours |
| **KPI 2** | Setup a FastAPI backend and a local PostgreSQL database with the pgvector extension. | 1.5 Hours |
| **KPI 3** | Create a Python script to ingest 10-20 mock meals into the Vector DB with semantic embeddings. | 1 Hour |
| **KPI 4** | Successfully connect the Frontend to the Backend so that moving the budget slider updates the results live. | 0.5 Hours |

---

## 📅 DAY 2: The "AI Meal Expert" Feature
**Objective**: Add depth and AI-powered insights to every meal.

| KPI | Task Description | Time |
| :--- | :--- | :--- |
| **KPI 1** | Create a Dynamic Route in Next.js (`/meals/[id]`) with a "Glassmorphism" design showing price, location, and metadata. | 2 Hours |
| **KPI 2** | Implement a FastAPI endpoint to fetch detailed meal info and simulated "Price History" data. | 1 Hour |
| **KPI 3** | Integrate a LangChain agent that generates a 2-sentence "AI Value Insight" for a meal (e.g., "This biryani has the highest protein-to-price ratio in F-8"). | 1.5 Hours |
| **KPI 4** | Display the AI insight on the frontend with a "sparkle" animation to highlight the agentic reasoning. | 0.5 Hours |

---

## 📅 DAY 3: The "Community & Automation" Feature
**Objective**: Build the systems that keep the data fresh and trustworthy.

| KPI | Task Description | Time |
| :--- | :--- | :--- |
| **KPI 1** | Build a "Report Price Change" form on the UI that allows users to input a new price and upload a photo. | 1.5 Hours |
| **KPI 2** | Create an ingestion API that saves these reports into a `pending_verifications` table in the database. | 1 Hour |
| **KPI 3** | Setup an n8n workflow that triggers when a new report is added and sends a notification to a mock "Admin Dashboard" or Telegram. | 1.5 Hours |
| **KPI 4** | Implement a "Confidence Score" logic in the backend that decreases a meal's score if many reports are pending. | 1 Hour |

---

## ✅ Final Success Criteria (After 15 Hours)
1. **Search**: I can search for "Cheap Burgers" and get semantic results locally.
2. **Detail**: I can see why a meal is recommended via an AI agent.
3. **Trust**: I can report a price change and see the automation trigger.

---

> [!IMPORTANT]
> To stay on track, do not spend more than the allotted time on any single KPI. If you get stuck, move to a "Mock" version and proceed to the next KPI to keep the momentum.
