# Hackathon Submission: Algomasters

## Team Details
**Team Name:** Algomasters

| Name | Email | Mobile | Roll Number | Branch |
| :--- | :--- | :--- | :--- | :--- |
| **Shivareddy** | Shivareddy.kottamittapally@gmail.com | 7997265275 | 24075A7205 | AI&DS |
| **Shaik Javeed** | iamshaik72@gmail.com | 9391187288 | 23071A7256 | AI&DS |
| **Puli Bhavishwa Reddy** | bhavishwareddy5@gmail.com | 8247696048 | 23071A7251 | AI&DS |

---

## Project Overview

Modern enterprises make thousands of high-impact decisions every day—from selecting AI vendors and approving procurement requests to evaluating policies and managing compliance. While Large Language Models (LLMs) are powerful, they struggle to make reliable enterprise decisions because they often lack business context, organizational goals, decision rules, and explainable reasoning. Traditional RAG systems improve retrieval but still operate primarily as question-answering systems rather than structured decision-making platforms.

Our solution is an **Enterprise Decision Intelligence Platform** that transforms organizational knowledge into a governed decision-making system. Instead of searching across an entire corporate knowledge base, organizations first build a centralized **Knowledge Library**, then create **Decision Workspaces** that define a specific business objective through goals, success metrics, business rules, decision points, and only the knowledge relevant to that decision.

When a user submits a decision request, the platform orchestrates a team of specialized AI agents that retrieve only workspace-approved knowledge, evaluate business rules, reason over the evidence, and generate a transparent recommendation supported by citations. Every recommendation remains human-in-the-loop, ensuring that AI assists decision makers rather than replacing them.

This architecture enables organizations to make context-aware, explainable, auditable, and reusable business decisions, turning enterprise knowledge into an intelligent decision system instead of another conversational chatbot.

---

## Repository
**GitHub Repository:** [https://github.com/codebyshivareddiee/enterprise-decision-intelligence-platform](https://github.com/codebyshivareddiee/enterprise-decision-intelligence-platform)

---

## Setup Instructions

### 1. Prerequisites
- **Node.js 18+** & npm
- **Python 3.11+**
- **Docker & Docker Compose** (Highly Recommended for backend)
- **[uv](https://docs.astral.sh/uv/)** (Recommended if running Python manually)

### 2. Environment Variables

Navigate to the `backend` directory and copy the template environment file:
```bash
cd backend
cp .env.example .env
```

Open `.env` and fill in your credentials. 

> [!NOTE]
> **Important Note for Judges:** We have included our actual **Qdrant API Key and URL** in the snippet below. We know that exposing keys in code is generally a bad practice, but we trust you as judges and are providing it directly to you so you don't have to waste time setting up a Qdrant Cloud cluster just to test our project. (This key is strictly not pushed to GitHub). You will still need to provide your own OpenAI API key and MongoDB URI.

**Example `.env` file:**
```env
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
APP_LOG_LEVEL=INFO
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Security
SECRET_KEY=change-me-to-a-random-secret-key-at-least-32-chars

# MongoDB Atlas
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<dbname>?retryWrites=true&w=majority
MONGODB_DB_NAME=decision_intelligence

# Qdrant Cloud (Provided for Judges to save time)
QDRANT_URL=https://<your-cluster>.qdrant.tech
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=knowledge_chunks

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o

# Feature Flags
ENABLE_ASYNC_LEARNER=true
```
*(Make sure to replace the placeholder MongoDB and OpenAI strings with your actual keys. You may leave the Qdrant keys as-is if provided.)*

### 3. Start the Backend

**Option A: Docker (Recommended)**
From the **root directory**, spin up the backend container:
```bash
docker compose up --build
```
*The backend API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

**Option B: Manual Execution**
From the `backend` directory, create and activate a virtual environment, install dependencies, and start the server:
```bash
uv venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -e ".[dev]"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the Frontend
The frontend connects locally to the backend API.

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
3. Install dependencies and start the UI:
   ```bash
   npm install
   npm run dev
   ```
   *Open [http://localhost:5173](http://localhost:5173) in your browser.*
