# 02 — Database Design

> Conceptual responsibilities only. No schemas yet.

---

## Responsibility Split

| Concern                    | Store        |
|---------------------------|--------------|
| Business state & identity | MongoDB Atlas |
| Vector embeddings & search | Qdrant Cloud |

These two stores are **never substituted for each other.** MongoDB does not store raw vectors. Qdrant does not store business objects.

---

## MongoDB Atlas — Collections

### Organizations
Represents a tenant. Owns all data within its boundary. No data crosses organization boundaries.

### Users
Authenticated individuals belonging to an organization. Roles and permissions are scoped per user.

### Workspaces
A working environment within an organization. References a knowledge schema, a set of knowledge assets, a lifecycle definition, and business rules. Multiple workspaces can coexist within one organization.

### Knowledge Schemas
Defines the structure and field types for knowledge assets in a specific domain (e.g., what fields a candidate profile or vendor proposal contains). Configuration, not code.

### Knowledge Assets
The actual data records or document references uploaded into a workspace. Each asset conforms to the workspace's knowledge schema. References the corresponding Qdrant collection for vector search.

### Lifecycle Definitions
Describes the stages a decision moves through (e.g., Under Review → Shortlisted → Decided). Configurable per workspace.

### Business Rules
Deterministic filter rules evaluated before AI reasoning. Examples: minimum score thresholds, mandatory field requirements, disqualifying conditions. Stored as structured configuration.

### Recommendations
The output of a completed recommendation workflow run. Contains ranked candidates or options, scores, applied rules, and links to the explanation.

### Decision History
A permanent, append-only record of every human decision made within a workspace. Used by the Learner to derive preferences.

### Preference Profiles
Learned preferences derived from decision history. Scoped to a workspace. Influences candidate ranking and reasoning in future runs.

### Conversations
Turn-by-turn message history for a user session within a workspace. Used to provide conversational context to the AI agents.

---

## Qdrant Cloud — Collections

### Document Chunks
Raw text segments produced by chunking knowledge asset documents during the upload workflow.

### Embedding Vectors
The vector representation of each document chunk, produced by `text-embedding-3-small`. Stored alongside the chunk for nearest-neighbor retrieval.

### Chunk Metadata
Lightweight metadata attached to each vector point: asset ID, workspace ID, organization ID, chunk index, and content type. Enables filtered vector search scoped to a workspace or asset.

### Asset References
Links each Qdrant point back to its source knowledge asset in MongoDB, enabling the Retriever to fetch full business context after a vector search.

---

## Key Constraints

- All MongoDB reads and writes are scoped by `organization_id` and `workspace_id`.
- Qdrant searches are always filtered by `workspace_id` to enforce tenant isolation.
- Decision History is append-only; records are never mutated or deleted.
- Preference Profiles are derived — they are never manually edited by users.
