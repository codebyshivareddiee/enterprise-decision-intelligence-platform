# Enterprise Decision Intelligence Platform — Backend

> Enterprise-grade, domain-agnostic Decision Intelligence Platform powered by FastAPI and OpenAI GPT-4o.

---

## Project Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker & Docker Compose (for containerised runs)

### Install locally with uv

```bash
# From the /backend directory
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -e ".[dev]"  # includes dev dependencies
```

### Copy environment variables

```bash
cp .env.example .env
# Edit .env with your real values (MongoDB URI, Qdrant URL, OpenAI key, etc.)
```

### Install pre-commit hooks

```bash
pre-commit install
```

---

## Run Locally

```bash
# From /backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the convenience script:

```bash
bash scripts/start.sh
```

The API will be available at:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Interactive OpenAPI docs |
| `http://localhost:8000/api/v1/health` | Liveness probe |
| `http://localhost:8000/api/v1/ready` | Readiness probe |

### Run tests

```bash
bash scripts/test.sh
# or directly:
pytest --cov=app -v
```

### Run linters

```bash
bash scripts/lint.sh
# or directly:
ruff check app tests
black --check app tests
mypy app
```

---

## Docker

### Build production image

```bash
# From /backend
docker build -t edip-backend:latest .
```

### Run production container

```bash
docker run --env-file .env -p 8000:8000 edip-backend:latest
```

### Run full stack (development)

```bash
# From project root
docker compose up --build
```

Health check: `GET http://localhost:8000/api/v1/health`

---

## Environment Variables

All variables are documented in [`.env.example`](.env.example). Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (`development`/`staging`/`production`) | `development` |
| `APP_PORT` | Port the server listens on | `8000` |
| `APP_LOG_LEVEL` | Log level (`DEBUG`/`INFO`/`WARNING`/`ERROR`) | `INFO` |
| `APP_CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:3000` |
| `SECRET_KEY` | Secret key for signing tokens | — |
| `MONGODB_URI` | MongoDB Atlas connection string | — |
| `MONGODB_DB_NAME` | MongoDB database name | `decision_intelligence` |
| `QDRANT_URL` | Qdrant Cloud cluster URL | — |
| `QDRANT_API_KEY` | Qdrant API key | — |
| `QDRANT_COLLECTION_NAME` | Qdrant collection for embeddings | `knowledge_chunks` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Chat model | `gpt-4o` |
| `ENABLE_ASYNC_LEARNER` | Enable background learner agent | `true` |

---

## Folder Explanation

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app factory + lifespan
│   ├── config/
│   │   └── settings.py       # Pydantic Settings — all env var loading
│   ├── core/
│   │   ├── constants.py      # Platform-wide constants (no magic strings)
│   │   ├── exceptions.py     # Domain exception hierarchy
│   │   ├── logging.py        # structlog configuration
│   │   └── routes.py         # Health + readiness endpoints
│   ├── models/               # Pydantic domain models (P2)
│   ├── repositories/         # Database access layer (P2/P3)
│   ├── services/             # Business logic services (P3+)
│   ├── agents/
│   │   ├── planner/          # Creates execution plans (P4)
│   │   ├── retriever/        # Vector search over knowledge (P7)
│   │   ├── reasoning/        # Business rules + GPT-4o scoring (P8)
│   │   ├── recommendation/   # Candidate ranking (P9)
│   │   ├── explanation/      # Human-readable explanations (P10)
│   │   └── learner/          # Preference profile updater (P11)
│   ├── orchestrator/         # Execution plan runner (P5)
│   ├── knowledge/            # Knowledge upload workflow (P3)
│   ├── memory/               # Conversation + decision history (P2+)
│   ├── prompts/              # GPT-4o prompt templates (.txt / .jinja2)
│   └── utils/                # Shared helpers and utilities
│
├── tests/
│   ├── test_smoke.py         # App startup + health endpoint tests
│   └── test_settings.py      # Settings validation tests
│
├── scripts/
│   ├── start.sh              # Start dev server locally
│   ├── lint.sh               # Run all linters
│   └── test.sh               # Run test suite
│
├── docker/
│   └── Dockerfile.dev        # Development image (hot-reload)
│
├── pyproject.toml            # Project metadata, Ruff, Black, mypy, pytest config
├── requirements.txt          # Pinned runtime dependencies
├── Dockerfile                # Multi-stage production image
├── .env.example              # Environment variable template
├── .pre-commit-config.yaml   # Pre-commit hooks (Ruff, Black, mypy, hygiene)
└── README.md                 # This file
```
