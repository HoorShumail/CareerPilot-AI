# ADR 004: Career Digital Twin as a Bounded Context

## Status
Accepted

## Context
The platform's signature feature is the "Career Digital Twin," a persistent AI persona representing the user's skills, goals, projects, and application history. This needs to be decoupled from standard generic LLM chat memory.

## Decision
We will treat the Career Digital Twin as a first-class Domain Bounded Context (`src/career_twin/`) rather than an implicit side-effect of conversational memory.

## Alternatives Considered
- **Standard Chat History (e.g., LangChain Memory)**: Fails to capture structured profile updates or long-term analytical tracking.
- **Tightly coupling to the User ORM Model**: Would result in a bloated God-object and blur the lines between authentication/profile data and AI-inferred state.

## Tradeoffs & Consequences
- **Pros**: Clear separation of concerns. The twin can have its own builders, updaters, and analyzers. We can independently evolve the logic that infers skills from resumes vs. user manual input.
- **Cons**: Adds architectural overhead, as we need a sync mechanism (`memory_sync.py`) to map traditional database data to the Twin's state representations.
