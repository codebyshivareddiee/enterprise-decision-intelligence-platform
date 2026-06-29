# Enterprise Decision Intelligence Platform

An enterprise-grade, domain-agnostic **Decision Intelligence Platform** designed to solve high-stakes organizational decisions using a multi-agent orchestrated pipeline.

The platform combines robust vector-based hybrid search, schema-conformant knowledge extraction, and probabilistic reasoning models to provide rank-ordered recommendations with human-interpretable rationale.

---

## Architecture Overview

The system is built on a decoupled, production-ready stack:

- **Backend**: FastAPI, MongoDB (persistent state), Qdrant (hybrid dense/sparse vector search), and OpenAI GPT-4o.
- **Frontend**: Vite + React, Vanilla CSS for premium dark/glassmorphic aesthetics.
- **Multi-Agent Orchestrator**: Executes a dynamically generated dependency graph of reasoning agents (Retriever, Reasoning, Rule Checker, Recommendation, Explanation, Learner).

### System Architecture
![Architecture Diagram](Diagrams/Architecture.png)

---

## Key Pipelines

### 1. Knowledge Ingestion & Indexing Pipeline
Ingests document payloads (PDFs, Markdown, Raw Text), parses structure using localized PDF tools, chunks, generates vector embeddings, and stores them in Qdrant for semantic retrieval.
![Knowledge Ingestion Pipeline](Diagrams/Knowledge%20Ingestion%20%26%20Indexing%20Pipeline.png)

### 2. Decision Intelligence Execution Pipeline
Executes decision plans dynamically through agent pipelines, retrieving evidence, reasoning through context, and applying business constraints to rank alternatives.
![Decision Intelligence Execution Pipeline](Diagrams/Decision%20Intelligence%20Execution%20Pipeline.png)

---

## Project Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- [uv](https://docs.astral.sh/uv/) (strongly recommended for Python package management)
- MongoDB & Qdrant credentials (local or cloud instances)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Configure environment variables**:
   Copy the template and edit `.env` with your API keys and database URIs:
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies**:
   Using `uv` (recommended):
   ```bash
   uv venv
   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   uv pip install -r requirements.txt
   uv pip install -e ".[dev]"
   ```
   *Alternatively, using standard pip:*
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or Windows equivalent
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

4. **Run the Backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The backend API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

5. **Run tests**:
   ```bash
   pytest --cov=app -v
   ```

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Configure environment variables**:
   Create a `.env` file pointing to the backend API:
   ```bash
   echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
   ```

3. **Install Node modules**:
   ```bash
   npm install
   ```

4. **Run the Frontend dev server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Docker Stack Execution

To run the entire system (Backend, Frontend, MongoDB, Qdrant) in local containerized mode:

```bash
# From the root directory
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
