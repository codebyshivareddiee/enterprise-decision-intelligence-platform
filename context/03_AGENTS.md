# 03 — Agent Catalog

> No implementation details. All agents are registered in the Agent Registry.
> For how agents are invoked, see `01_ARCHITECTURE.md`.

---

## Planner

**Purpose:** Translates a user goal into a structured, executable plan.

**Responsibilities:**
- Understand the user's intent from the workspace context.
- Decompose the goal into an ordered sequence of agent tasks.
- Specify dependencies between tasks.
- Return a plan — not results.

**Inputs:**
- User goal (natural language)
- Workspace context (schema, lifecycle, active business rules)
- Conversation history

**Outputs:**
- Execution plan: ordered list of `{ agent, task, inputs, depends_on }` steps

---

## Retriever

**Purpose:** Fetch the most relevant knowledge chunks for a given query.

**Responsibilities:**
- Embed the query using `text-embedding-3-small`.
- Perform filtered nearest-neighbor search in Qdrant scoped to the workspace.
- Return ranked chunks with their MongoDB asset references.
- Apply any pre-filter metadata constraints (e.g., asset type, date range).

**Inputs:**
- Query text
- Workspace ID
- Optional metadata filters

**Outputs:**
- List of `{ chunk_text, asset_id, score, metadata }` results

---

## Business Context & Reasoning Agent

**Purpose:** Apply business rules and perform AI reasoning over retrieved candidates.

**Responsibilities:**
- Evaluate deterministic business rules against each candidate (via Rule Engine).
- Discard candidates that fail hard rules.
- Apply GPT-5 reasoning over remaining candidates using workspace context and preferences.
- Produce structured scores and reasoning notes per candidate.

**Inputs:**
- Candidate list (from Retriever)
- Business rules (from workspace)
- Preference profile (from MongoDB)
- Knowledge schema

**Outputs:**
- Scored candidate list: `{ candidate_id, rule_result, ai_score, reasoning_notes }`

---

## Recommendation Agent

**Purpose:** Produce a final ranked recommendation from scored candidates.

**Responsibilities:**
- Combine rule results and AI scores into a final ranking.
- Apply any workspace-level ranking weights.
- Select top-N recommendations.
- Tag each recommendation with the contributing factors.

**Inputs:**
- Scored candidate list (from Reasoning Agent)
- Workspace ranking configuration

**Outputs:**
- Ranked recommendation list: `{ rank, candidate_id, final_score, contributing_factors }`

---

## Explanation Agent

**Purpose:** Generate a human-readable explanation for each recommendation.

**Responsibilities:**
- Summarize why each recommended candidate ranked where it did.
- Reference specific knowledge assets, rules, and reasoning notes.
- Produce concise, plain-language rationales suitable for business reviewers.

**Inputs:**
- Ranked recommendation list
- Candidate reasoning notes
- Knowledge schema (for field label mapping)

**Outputs:**
- Explanation list: `{ candidate_id, explanation_text, cited_assets }`

---

## Learner

**Purpose:** Update the workspace preference profile based on confirmed human decisions.

**Responsibilities:**
- Listen for human decision events (approve / reject / rank-override).
- Extract preference signals from the decision (which attributes influenced acceptance vs. rejection).
- Update the workspace preference profile in MongoDB.
- Do not retrain models — only update preference configuration.

**Inputs:**
- Decision event: `{ workspace_id, recommendation_id, human_decision, feedback_notes }`
- Current preference profile

**Outputs:**
- Updated preference profile stored in MongoDB

> The Learner runs asynchronously and is **event-driven**. It does not block the recommendation workflow.
