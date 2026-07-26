# ADR 005: RAG Architecture using ChromaDB

## Status
Accepted

## Context
To power Job Recommendation, Skill Gap Analysis, and Mock Interviews, the agents need contextual access to a vast corpus of Job Descriptions, past resumes, and interview questions.

## Decision
We will implement Retrieval-Augmented Generation (RAG) using **ChromaDB** as the local vector store, abstracted behind our `src/infrastructure/vectordb/` layer.

## Alternatives Considered
- **Pinecone / Weaviate Cloud**: Adds external dependency and potential latency/cost during early development phases.
- **pgvector**: Convenient since we already use PostgreSQL, but requires specific DB extensions and is slightly more complex to orchestrate for pure text embedding search compared to purpose-built stores like ChromaDB initially.

## Tradeoffs & Consequences
- **Pros**: ChromaDB runs locally, is easy to deploy via Docker Compose, and integrates perfectly with LangChain/LangGraph.
- **Cons**: May require migration to a managed vector database (like Pinecone) or pgvector when scaling to millions of documents. The infrastructure layer abstraction mitigates this risk.
