# ADR 003: Use LangGraph for Multi-Agent Orchestration

## Status
Accepted

## Context
The system requires complex multi-agent workflows, such as a Resume Parser passing data to a Job Matcher, or a Mock Interviewer reacting to user input iteratively with state persistence.

## Decision
We will use **LangGraph** to model these interactions as stateful graphs.

## Alternatives Considered
- **LangChain (Standard)**: Too rigid for cyclic or non-linear agent communication.
- **Autogen**: Good for conversational agents but harder to integrate tightly into a deterministic backend API flow with strict typed state.
- **CrewAI**: Higher level abstraction, but less control over the underlying graph execution and state persistence mechanisms.

## Tradeoffs & Consequences
- **Pros**: Explicit state management (`AgentState`), ability to handle cyclic graphs (e.g., Critic loops), and checkpointing capabilities for long-running workflows.
- **Cons**: Steeper learning curve compared to standard sequential chains.
