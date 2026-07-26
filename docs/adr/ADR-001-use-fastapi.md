# ADR 001: Use FastAPI for the Backend API

## Status
Accepted

## Context
CareerPilot-AI requires a high-performance, asynchronous backend capable of streaming LLM responses, handling concurrent user sessions, and easily integrating with modern Python libraries (LangGraph, SQLAlchemy async).

## Decision
We will use **FastAPI** as the core web framework for the backend.

## Alternatives Considered
- **Flask**: Lacks native async support and built-in validation.
- **Django**: Too monolithic and heavy for a microservices/agent-oriented architecture.
- **Express (Node.js)**: Would split the codebase between Python (AI/Data) and TypeScript (API), increasing complexity.

## Tradeoffs & Consequences
- **Pros**: Automatic OpenAPI documentation, native `async`/`await` support, excellent Pydantic integration for schema validation, high performance (Starlette/Uvicorn).
- **Cons**: Less built-in tooling compared to Django (requires assembling our own ORM, migration, and auth stack).
