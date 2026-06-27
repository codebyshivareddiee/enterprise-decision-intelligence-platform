# 04 — Core Workflows

> High-level sequence descriptions only. For agent details see `03_AGENTS.md`.

---

## 1. Knowledge Upload Workflow

**Trigger:** User uploads a document or data record into a workspace.

```
User uploads file or record
         │
         ▼
Validate against Knowledge Schema
         │
         ▼
Store asset record in MongoDB (Knowledge Assets)
         │
         ▼
Extract and chunk document text
         │
         ▼
Embed each chunk (text-embedding-3-small)
         │
         ▼
Store vectors + metadata in Qdrant (scoped to workspace)
         │
         ▼
Asset is available for retrieval
```

**Key rules:**
- Upload is rejected if the asset does not conform to the workspace's Knowledge Schema.
- Qdrant points always include `workspace_id` and `organization_id` in metadata.
- Re-uploading an asset replaces its existing Qdrant points (no duplicates).

---

## 2. Recommendation Workflow

**Trigger:** User submits a goal or decision request within a workspace.

```
User submits goal
         │
         ▼
Planner creates execution plan
         │
         ▼
Orchestrator executes plan:
    │
    ├──► Retriever → fetch relevant knowledge chunks
    │
    ├──► Business Context & Reasoning Agent
    │         → apply rules, score candidates
    │
    ├──► Recommendation Agent
    │         → rank and select top-N
    │
    └──► Explanation Agent
              → generate rationales
         │
         ▼
Recommendation + Explanations stored in MongoDB
         │
         ▼
Presented to human reviewer
```

**Key rules:**
- Business rules are evaluated before AI reasoning. Hard-failing candidates are excluded.
- The Planner's output is inspectable — the plan is logged before execution.
- The full recommendation with explanations is persisted before human review begins.

---

## 3. Learning Workflow

**Trigger:** Human reviewer submits a decision (approve / reject / override ranking).

```
Human submits decision
         │
         ▼
Decision event written to Decision History (append-only)
         │
         ▼
Learner agent triggered asynchronously
         │
         ▼
Learner extracts preference signals from decision
         │
         ▼
Preference Profile updated in MongoDB
         │
         ▼
Future recommendations influenced by updated profile
```

**Key rules:**
- Decision History is never mutated — only appended.
- The Learner never modifies model weights — only preference configuration.
- Preference updates are workspace-scoped; they do not affect other workspaces.
- If the Learner fails, the decision is still recorded — learning is best-effort.
