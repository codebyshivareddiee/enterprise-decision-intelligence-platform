# 06 — Implementation Tickets

> Each ticket is independently implementable. Complete P1 before starting others.
> For coding conventions see `05_CODING_RULES.md`. For architecture see `01_ARCHITECTURE.md`.

---

## P1 — Project Structure

Set up monorepo layout with `/backend` (FastAPI) and `/frontend` (React + Tailwind) directories.
Configure Docker Compose for local development.
Add environment variable templates (`.env.example`).
Wire up MongoDB Atlas and Qdrant Cloud connections (no business logic yet — just connectivity).

**Done when:** `docker compose up` starts backend + frontend with health check endpoints responding.

---

## P2 — Domain Models

Define all Pydantic models for MongoDB collections:
Organizations, Users, Workspaces, Knowledge Schemas, Knowledge Assets, Lifecycle Definitions,
Business Rules, Recommendations, Decision History, Preference Profiles, Conversations.

**Done when:** All models are importable with no runtime errors and pass basic unit tests.

---

## P3 — Knowledge Layer

Implement Knowledge Schema and Knowledge Asset repositories.
Implement the Knowledge Upload Workflow (validate → store in MongoDB → chunk → embed → store in Qdrant).
Implement the Embedding Service wrapper around `text-embedding-3-small`.

**Done when:** A document can be uploaded, chunked, embedded, and retrieved via vector search.

---

## P4 — Planner

Implement the Planner agent.
Given a user goal and workspace context, produce a structured execution plan.
Execution plan format: ordered list of `{ agent, task, inputs, depends_on }`.

**Done when:** Planner returns valid plans for a set of test goals without hallucinating agent names not in the Agent Registry.

---

## P5 — Orchestrator

Implement the Orchestrator service.
Accepts a plan from the Planner, resolves agents from the Agent Registry, executes steps in order, and passes outputs between steps.

**Done when:** Orchestrator can execute a two-step plan (Retriever → Reasoning Agent) end-to-end.

---

## P6 — Agent Registry

Implement the Agent Registry as a simple in-memory or config-file-based catalog.
Each entry: agent name, description, input contract, output contract, callable reference.

**Done when:** Orchestrator resolves all six agents by name and the registry raises a clear error for unknown agent names.

---

## P7 — Retriever Agent

Implement the Retriever agent.
Embed query → filtered Qdrant search (workspace-scoped) → return ranked chunks with asset references.

**Done when:** Given a text query and workspace ID, returns relevant chunks from previously uploaded knowledge assets.

---

## P8 — Business Context & Reasoning Agent

Implement the Business Context & Reasoning Agent.
Evaluate business rules (Rule Engine) → exclude failing candidates → GPT-5 reasoning over remainder → return scored candidates.

**Done when:** Given a candidate list and business rules, returns scored candidates with reasoning notes and correctly excludes hard-rule failures.

---

## P9 — Recommendation Agent

Implement the Recommendation Agent.
Combine rule results and AI scores → apply ranking weights → select top-N → tag contributing factors.

**Done when:** Given scored candidates, returns a ranked recommendation list.

---

## P10 — Explanation Agent

Implement the Explanation Agent.
Generate plain-language explanations for each recommendation citing specific rules, scores, and knowledge assets.

**Done when:** Each recommendation in the list has a readable explanation referencing real data from the run.

---

## P11 — Learner Agent

Implement the Learner agent.
Listen for decision events → extract preference signals → update Preference Profile in MongoDB.
Run asynchronously (background task or queue).

**Done when:** After a human decision, the preference profile is updated and influences the next recommendation run.

---

## P12 — Integration Tests

Write end-to-end integration tests for:
- Knowledge Upload Workflow (P3)
- Full Recommendation Workflow (P4 → P10)
- Learning Workflow (P11)

**Done when:** All three workflows pass integration tests against real (or mocked) MongoDB and Qdrant instances.

---

## P13 — FastAPI Routes

Expose REST endpoints for:
- Workspace management (CRUD)
- Knowledge asset upload
- Recommendation request (trigger workflow)
- Human decision submission
- Conversation history

Add authentication middleware (API key or JWT — TBD).

**Done when:** All endpoints are documented in OpenAPI and tested via integration tests.

---

## P14 — React UI

Build the frontend:
- Workspace selector / dashboard
- Knowledge asset upload interface
- Recommendation review interface (ranked list + explanations)
- Decision submission (approve / reject / override)
- Conversation / chat interface for goal input

**Done when:** A non-technical user can complete the full recommendation workflow through the UI without touching the API directly.
