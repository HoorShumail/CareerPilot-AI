# ADR 002: Use PostgreSQL for Relational Persistence

## Status
Accepted

## Context
The platform needs to store structured user data (profiles, job applications, interview histories) alongside semi-structured data (agent execution logs, nested skill requirements).

## Decision
We will use **PostgreSQL** as the primary relational database, accessed asynchronously via `asyncpg` and `SQLAlchemy`.

## Alternatives Considered
- **SQLite**: Insufficient for multi-user concurrency in production.
- **MongoDB**: While good for documents, we have highly relational entities (User -> Applications -> Interviews) that benefit from ACID compliance and SQL joins.

## Tradeoffs & Consequences
- **Pros**: Robust, ACID compliant, excellent `JSONB` support for storing semi-structured Digital Twin memories and raw AI outputs.
- **Cons**: Requires managing a separate database service and schema migrations (Alembic) compared to schemaless NoSQL.
