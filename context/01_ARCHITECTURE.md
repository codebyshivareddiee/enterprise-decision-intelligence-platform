# 01 — High-Level Architecture

> No implementation details. For invariants, see `DO_NOT_CHANGE.md`.

---

## System Flow

```
User Request
     │
     ▼
 Workspace  ──────────────────── Knowledge Layer
     │                                 │
     ▼                                 │
  Planner  ◄────────────────────────── ┘
     │
     ▼
Orchestrator
     │
     ├──► Retriever Agent
     ├──► Business Context & Reasoning Agent
     ├──► Recommendation Agent
     └──► Explanation Agent
              │
              ▼
         Human Review
              │
              ▼
           Learner
```

---

## Components

### Workspace

The top-level tenant context. Each workspace belongs to an organization and references a set of knowledge assets, lifecycle definitions, and business rules. All operations are scoped to a workspace.

### Knowledge Layer

Manages the organization's domain knowledge. Consists of:
- **Knowledge Schemas** — define the structure of knowledge assets for a domain.
- **Knowledge Assets** — the actual uploaded documents, profiles, or data records.
- **Embeddings** — vector representations of knowledge chunks stored in Qdrant.

The Knowledge Layer is read-only during inference; it is updated only via the Knowledge Upload Workflow.

### Planner

Accepts a user goal and workspace context. Produces a structured execution plan (a sequence of agent tasks with dependencies). Does not execute anything — planning is its only responsibility.

### Orchestrator

Receives an execution plan from the Planner and executes it step by step. Coordinates agent calls, passes outputs between steps, handles retries, and collects results. Stateless between executions.

### Agent Registry

A catalog of available agents with their capability contracts (inputs, outputs, purpose). The Orchestrator resolves agent names from the registry at runtime. Agents are registered, not hard-coded into the Orchestrator.

### Supporting Services

- **Embedding Service** — wraps `text-embedding-3-small`; used during knowledge upload and retrieval.
- **Rule Engine** — evaluates deterministic business rules against candidate data before AI reasoning.
- **Conversation Service** — stores and retrieves conversation history per workspace session.

### Recommendation Pipeline

```
Retrieve relevant knowledge chunks
     │
     ▼
Apply business rules (deterministic filter)
     │
     ▼
AI reasoning over remaining candidates
     │
     ▼
Generate ranked recommendations
     │
     ▼
Generate explanations
     │
     ▼
Present to human reviewer
```

### Learning Pipeline

```
Human approves or rejects recommendation
     │
     ▼
Learner captures decision event
     │
     ▼
Update preference profile for workspace
     │
     ▼
Preference profile influences future recommendations
```

The Learner is event-driven and runs asynchronously after human review.
