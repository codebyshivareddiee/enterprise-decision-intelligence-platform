"""Prometheus metrics definitions for the platform."""

from prometheus_client import Counter, Gauge, Histogram

# ── API Metrics ─────────────────────────────────────────────────────────────

REQUESTS_TOTAL = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── AI Layer Metrics ────────────────────────────────────────────────────────

LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "operation", "status"],
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM request duration in seconds",
    ["provider", "model", "operation"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

LLM_TOKENS = Counter(
    "llm_tokens_total",
    "Total number of tokens processed by LLM",
    ["provider", "model", "token_type"],  # token_type: prompt, completion
)

# ── Workflow & Agent Metrics ────────────────────────────────────────────────

WORKFLOWS_TOTAL = Counter(
    "workflows_total",
    "Total number of workflow executions",
    ["status"],
)

WORKFLOW_DURATION = Histogram(
    "workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["status"],
    buckets=[1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0],
)

AGENT_EXECUTIONS_TOTAL = Counter(
    "agent_executions_total",
    "Total number of agent executions",
    ["agent_type", "status"],
)

AGENT_DURATION = Histogram(
    "agent_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type"],
    buckets=[0.5, 1.0, 5.0, 15.0, 30.0, 60.0],
)

AGENT_ARTIFACTS = Counter(
    "agent_artifacts_total",
    "Total number of artifacts consumed or produced by agents",
    ["agent_type", "artifact_action"],  # artifact_action: consumed, produced
)

# ── Knowledge Layer Metrics ─────────────────────────────────────────────────

DOCUMENTS_PROCESSED_TOTAL = Counter(
    "documents_processed_total",
    "Total number of documents processed during ingestion",
    ["status", "chunk_strategy"],
)

DUPLICATE_DOCUMENTS_TOTAL = Counter(
    "duplicate_documents_total",
    "Total number of duplicate documents detected",
)

CHUNKING_DURATION = Histogram(
    "chunking_duration_seconds",
    "Document chunking duration in seconds",
    ["chunk_strategy"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

KNOWLEDGE_DEFAULTS_USED = Counter(
    "schema_defaults_used_total",
    "Total number of times schema defaults were used",
)

RULE_BASED_DECISIONS = Counter(
    "rule_based_decisions_total",
    "Total number of rule-based decisions during extraction",
)

AI_OVERRIDE_DECISIONS = Counter(
    "ai_override_decisions_total",
    "Total number of AI override decisions during extraction",
)

# ── Workspace Metrics ───────────────────────────────────────────────────────

WORKSPACE_ASSETS = Gauge(
    "workspace_assets_current",
    "Current number of knowledge assets in the workspace",
    ["workspace_id"],
)

WORKSPACE_SCHEMAS = Gauge(
    "workspace_schemas_current",
    "Current number of distinct schemas in use within the workspace",
    ["workspace_id"],
)

WORKSPACE_RULES = Gauge(
    "workspace_rules_current",
    "Current number of rules in the workspace",
    ["workspace_id"],
)
