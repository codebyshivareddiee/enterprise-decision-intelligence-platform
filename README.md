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

### 1. Prerequisites
Before running the platform, ensure you have the following installed:
- **Node.js 18+** & npm (for the frontend)
- **Python 3.11+** (for manual backend setup)
- **Docker & Docker Compose** (optional, for containerized backend)
- **[uv](https://docs.astral.sh/uv/)** (strongly recommended for Python package management if running manually)

> [!IMPORTANT]
> **Cloud Databases Required:** This project does NOT run MongoDB or Qdrant locally via Docker. You must provision external databases (e.g., MongoDB Atlas and Qdrant Cloud) and provide their connection URIs in your `.env` file.

---

### 2. Environment Configuration (Backend)

The backend requires valid database URIs and an OpenAI API key to function.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the template environment file:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and fill in your credentials:
   - `OPENAI_API_KEY`
   - `MONGODB_URI`
   - `QDRANT_URL` and `QDRANT_API_KEY`

---

### 3. Running the Backend

You can run the backend either via Docker (Recommended) or Manually.

#### Option A: Docker (Recommended)
From the **root directory**, spin up the backend container:
```bash
docker compose up --build
```
*The backend API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

#### Option B: Manual Execution
1. From the `backend` directory, create and activate a virtual environment using `uv`:
   ```bash
   uv venv
   
   # Activate (Windows)
   .venv\Scripts\activate
   # Activate (macOS/Linux)
   source .venv/bin/activate
   ```
2. Install dependencies and start the server:
   ```bash
   uv pip install -r requirements.txt
   uv pip install -e ".[dev]"
   
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

### 4. Running the Frontend

The frontend is a React + Vite application that runs locally and connects to the backend API.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Configure the environment variables:
   ```bash
   # Linux/macOS
   echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
   
   # Windows (PowerShell)
   echo "VITE_API_URL=http://localhost:8000/api/v1" | Out-File -Encoding UTF8 .env
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
   *Open [http://localhost:5173](http://localhost:5173) in your browser to access the platform.*
