# 🥗 Foodly: Agentic AI Food Discovery

Foodly is an **Agentic Food Discovery Ecosystem** designed to provide hyper-localized, budget-conscious meal recommendations. It uses a reasoning engine to understand context, value-for-money, and real-time market fluctuations.

See the [Execution Plan](execution_plan.md) for the 3-day development roadmap.

---

## 🛠 Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL (Local Instance)
- **AI Integration**: LangGraph + Google GenAI (Gemini)

---

## 🚀 Local Setup Instructions

This project runs entirely in a local development environment. No Docker required.

### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **PostgreSQL** (v15+)

### 2. Database Setup
1. Install PostgreSQL locally on your machine.
2. Create a new database named `foodly_db`.
3. Set up your username and password.
4. (Optional) Install the `pgvector` extension if you plan to use AI semantic search later.

### 3. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update `DATABASE_URL` with your local PostgreSQL credentials:
     ```
     DATABASE_URL=postgresql://postgres:password@localhost:5432/foodly_db
     ```
5. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### 4. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

---

## 📂 Project Structure

```text
foodly-platform/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes
│   │   ├── core/            # Config, database setup
│   │   ├── models/          # SQLAlchemy definitions
│   │   └── schemas/         # Pydantic models
│   ├── main.py              # Entry point
│   └── .env                 # Local environment variables
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components
│   │   └── app/             # Next.js App Router
└── README.md
```

---

## 📍 API Endpoints
Once the backend is running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔮 Future Enhancements
- **Agentic Swarm**: Implementing multi-agent workflows with LangGraph.
- **Semantic Search**: Utilizing `pgvector` for "similar vibe" meal discovery.
- **Price Tracking**: Automated price verification and history.
