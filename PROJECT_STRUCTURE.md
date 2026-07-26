# CareerPilot-AI Project Structure

This document outlines the Clean Architecture and Domain-Driven Design (DDD) boundaries of the CareerPilot-AI project. This architecture ensures high maintainability, testability, and scalability.

## Root Directories

### `src/` (Backend Application)
Contains the core FastAPI application, LangGraph agents, and all business logic.

- **`agents/`**: Domain-based agent modules. Each module (e.g., `resume/`, `interview/`) contains the nodes, graphs, and tools specific to that agent's domain.
- **`career_twin/`**: The bounded context for the Career Digital Twin. Handles the long-term memory aggregation and lifecycle of the user's AI persona.
- **`config/`**: Configuration management using Pydantic `BaseSettings`. Handles environment variables, logging setup, and database connections.
- **`constants/`**: Immutable constants (roles, skills, agent names) separated from environment configurations.
- **`core/`**: Internal domain models and shared business entities that are not explicitly tied to DB or API structures.
- **`db/`**: Infrastructure layer for data persistence. Contains SQLAlchemy ORM `models/`, Alembic `migrations/`, and abstract `repositories/`.
- **`exceptions/`**: Domain-specific Python exceptions to standardize error handling across the application.
- **`infrastructure/`**: External dependencies and third-party integrations (LLMs, VectorDBs, Redis, Email, etc.). Business logic depends on abstractions, while this layer implements them.
- **`prompts/`**: Centralized, versionable LLM prompt templates segmented by domain.
- **`schemas/`**: Pydantic models acting as Data Transfer Objects (DTOs) for API request validation and response formatting.
- **`services/`**: The core application logic. Services orchestrate repositories, agents, and infrastructure to execute business use cases. API routes should only call services.
- **`api/`**: The delivery mechanism. Contains FastAPI `routes/`, `middleware/`, and `dependencies.py`. Controllers remain extremely thin.

### `web/` (Frontend Application)
The Streamlit-based web interface.

- **`app.py`**: The entry point.
- **`pages/`**: Individual Streamlit views.
- **`components/`**: Reusable UI components (e.g., sidebars, metrics cards).
- **`api_client.py`**: HTTP client to interact with the backend API securely.

### `docs/` (Documentation)
Comprehensive system documentation.

- **`adr/`**: Architecture Decision Records detailing significant technical choices.
- **`architecture/`**: High-level system design documents.
- **`api/`**: API specifications and usage guides.

## Dependency Direction
Following Clean Architecture principles, dependencies must point inwards:
`API Routes / Agents` → `Services` → `Core Domain Models` / `Repositories`

**Rule of Thumb:**
- Business logic belongs in `services/`.
- External API calls belong in `infrastructure/`.
- Pydantic models for API go to `schemas/`, SQLAlchemy to `db/models/`.

## Where to Add New Code
- **New API Endpoint:** Add schema to `src/schemas/`, business logic to `src/services/`, route to `src/api/routes/`.
- **New Agent Workflow:** Add prompts to `src/prompts/`, agent logic to `src/agents/<domain>/`, and orchestrate it from a service.
- **New Database Table:** Add model to `src/db/models/`, run `alembic revision --autogenerate`, add repository in `src/db/repositories/`.
