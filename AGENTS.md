# AGENTS.md

## Project Overview

This repository is a prototype of a policy-aware AI code review workflow for a retail checkout service.

It demonstrates:
- developer workflow integration
- PR diff review
- policy grounding with RAG
- hybrid retrieval
- evals
- observability
- human-in-the-loop review

## Repository Structure

- `app/main.py`: FastAPI retail checkout service
- `tests/`: pytest test suite
- `policies/`: company policy documents
- `review_agent.py`: AI PR review workflow
- `rag_setup.py`: indexes policy documents into ChromaDB
- `rag_query.py`: tests semantic retrieval
- `logs/`: local review logs, not committed

## Important Commands

Run the app:

```bash
python3 -m uvicorn app.main:app --reload
