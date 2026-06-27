# DO NOT CHANGE — Architectural Invariants

> These decisions are **locked**. They define what the system is.
> Changing any of these requires explicit, unanimous team agreement and a full document update.

---

## Data Ownership

- **Knowledge belongs to Organizations.** No knowledge asset, embedding, or preference profile may be read, referenced, or used by any other organization.
- **Workspaces reference Organization knowledge.** A workspace cannot import or link knowledge from another organization.
- **All database operations are scoped by `organization_id` and `workspace_id`.**

---

## System Responsibilities

- **Planner only creates execution plans.** It does not call agents, fetch data, or produce business outputs.
- **Orchestrator only executes execution plans.** It does not modify plans or apply business logic.
- **Business Rules are deterministic.** They are never delegated to AI. Hard-failing rules always exclude candidates — no exceptions, no overrides by GPT-5.
- **AI performs reasoning only.** GPT-5 scores and reasons over candidates that have already passed business rules. It does not make final decisions — humans do.

---

## Data Stores

- **MongoDB stores business state.** All structured domain data (organizations, workspaces, assets, rules, recommendations, decisions, preferences, conversations) lives in MongoDB.
- **Qdrant stores embeddings only.** Raw vectors and chunk metadata live in Qdrant. No business objects. No duplicating MongoDB data in Qdrant.
- **Decision History is append-only.** Records are never updated or deleted. This is the permanent audit trail.

---

## Learning

- **Learner is event-driven.** It runs asynchronously after human decisions. It never blocks the recommendation workflow.
- **Learner updates preference configuration only.** It does not fine-tune or retrain models.
- **Preference Profiles are workspace-scoped.** Preferences learned in one workspace do not affect any other workspace.

---

## Technology Stack

- **The technology stack is fixed.** React, Tailwind CSS, Python, FastAPI, OpenAI GPT-5, text-embedding-3-small, MongoDB Atlas, Qdrant Cloud, Docker, Vercel, Render.
- **No alternative AI providers.** Only OpenAI APIs are used for embeddings and reasoning.

---

## Product Principles

- **The platform must remain domain-agnostic.** No domain-specific logic (e.g., hiring-specific rules) may be hard-coded into the platform. All domain behavior is configuration.
- **Explainability is non-negotiable.** Every recommendation must include a human-readable explanation. Unexplained recommendations must not be surfaced to users.
- **The architecture must remain simple enough to be implemented by three engineers within three days.** Complexity is the primary risk. When in doubt, choose the simpler approach.
