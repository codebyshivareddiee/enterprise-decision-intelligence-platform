# 00 — Project Overview

## Vision

A generic, configurable **Enterprise Decision Intelligence Platform** that helps organizations make consistent, explainable, and continuously improving decisions across any business domain.

Hackathon demo use case: **Hiring AI Engineers**.

---

## Goals

- Automate complex multi-criteria decision workflows using AI reasoning.
- Enforce organization-defined business rules deterministically.
- Surface explainable recommendations with full audit trails.
- Learn from human decisions to continuously improve recommendations.
- Remain configurable for any business domain without code changes.

---

## Scope

- Multi-tenant workspace model with organization-owned knowledge.
- Configurable knowledge schemas per workspace.
- AI-powered reasoning over structured and unstructured knowledge assets.
- Human-in-the-loop review and feedback loop.
- Decision history and preference learning.

---

## Non-Goals

- Not a hiring platform — the demo use case does not define the product.
- No real-time data streaming or event sourcing infrastructure.
- No native mobile application.
- No self-hosted LLM inference — only OpenAI APIs.
- No multi-cloud or on-premise deployment in v1.

---

## Technology Stack

| Layer        | Technology                          |
|-------------|--------------------------------------|
| Frontend    | React, Tailwind CSS                  |
| Backend     | Python, FastAPI                      |
| AI          | OpenAI GPT-5, text-embedding-3-small |
| Database    | MongoDB Atlas                        |
| Vector DB   | Qdrant Cloud                         |
| Deployment  | Docker, Vercel (frontend), Render (backend) |

> **This stack is fixed. Do not propose alternatives.**

---

## Core Product Principles

1. **Organizations own knowledge.** No data crosses tenant boundaries.
2. **Rules before AI.** Business rules are evaluated deterministically before AI reasoning begins.
3. **Explainability is mandatory.** Every recommendation includes a human-readable rationale.
4. **Domain-agnostic by design.** Schemas, rules, and lifecycles are configuration, not code.
5. **Humans close the loop.** The system learns only from confirmed human decisions.
6. **Simplicity over cleverness.** The architecture must be implementable by three engineers in three days.
