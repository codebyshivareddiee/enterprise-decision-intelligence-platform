# 05 — Engineering Conventions

> All contributors (human and AI) must follow these rules. No exceptions without team agreement.

---

## Architecture

### Clean Architecture
Separate concerns into layers: API routes → Services → Repositories → Domain models.
Dependencies point inward only — inner layers never import from outer layers.

### Dependency Injection
Pass dependencies (repositories, services, clients) via constructors or FastAPI `Depends()`.
Never instantiate dependencies inside business logic.

### Repository Pattern
All database access goes through a repository class.
Services never call MongoDB or Qdrant directly — only through repositories.

### Service Layer
Business logic lives in service classes, not in route handlers.
A route handler's only job: parse request → call service → return response.

### No Business Logic in Routes
FastAPI route handlers must be thin. Validation, orchestration, and computation belong in services or agents.

---

## Backend (Python / FastAPI)

### Async First
Use `async def` for all route handlers, service methods, and repository methods.
Use `motor` for async MongoDB access. Use the async Qdrant client.

### Pydantic Models
All request bodies, response bodies, and internal data transfer objects are Pydantic models.
Never pass raw dicts across layer boundaries.

### Type Hints Everywhere
All function signatures must include full type hints — parameters and return types.
Use `Optional`, `List`, `Dict` from `typing` (or built-in generics in Python 3.10+).

### Small Functions
Functions do one thing. If a function exceeds ~30 lines, it should be decomposed.
Prefer named helper functions over inline complexity.

### Externalized AI Prompts
All GPT-5 prompt templates live in a dedicated `prompts/` directory as `.txt` or `.jinja2` files.
Prompts are never hard-coded inline inside agent logic.

### Error Handling
Use custom exception classes per domain (e.g., `KnowledgeAssetNotFoundError`).
Route handlers catch domain exceptions and map them to appropriate HTTP status codes.

---

## Frontend (React / Tailwind CSS)

### Modular Components
One component per file. Components are small and composable.
Shared UI primitives live in `components/ui/`. Feature components live in `components/features/`.

### No Business Logic in Components
Components handle rendering and user events only.
Data fetching, transformation, and state management live in hooks or service modules.

### Prefer Composition over Inheritance
Build complex UI by composing small components.
Avoid class components and inheritance hierarchies.

### Consistent Naming
Components: `PascalCase`. Hooks: `useCamelCase`. Files: `kebab-case.tsx`.

---

## General

### No Magic Numbers or Strings
All constants are named and defined in a `constants` module.

### No Silent Failures
Every caught exception must be logged. Never swallow errors with an empty `except` or `.catch(() => {})`.

### Consistency Over Cleverness
Prefer readable, predictable code over clever one-liners.
Code is written for the next engineer (or AI agent) to understand immediately.

### Commit Discipline
Each commit is atomic and represents one logical change.
Commit messages follow: `type(scope): short description` (e.g., `feat(retriever): add metadata filter support`).
