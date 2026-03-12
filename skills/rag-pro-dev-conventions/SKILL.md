---
name: rag-pro-dev-conventions
description: Project-specific development conventions for the ContextPilot repository. Use when working in this repo on the Vue frontend, Flask backend, LangChain or LangGraph RAG pipelines, API contracts, technical docs, or memory and retrieval features that must stay aligned with the existing scaffold and docs/01-04.
---

# Rag Pro Dev Conventions

## Overview

Use this skill to keep changes in the ContextPilot repo consistent with the existing scaffold, API DTOs, frontend page contracts, and LLM application design. Read the matching docs file before changing behavior:

- Architecture: [`docs/01-architecture.md`](../../docs/01-architecture.md)
- Backend API: [`docs/02-backend-api.md`](../../docs/02-backend-api.md)
- Frontend spec: [`docs/03-frontend-spec.md`](../../docs/03-frontend-spec.md)
- LLM/RAG/Agent guide: [`docs/04-llm-rag-agent-guide.md`](../../docs/04-llm-rag-agent-guide.md)

## Apply The Repo Rules

- Keep `user_id` in all backend resource boundaries until full auth exists.
- Keep API field names aligned across:
  - `backend/app/models/schemas.py`
  - `frontend/src/types/index.ts`
  - `docs/02-backend-api.md`
- Prefer changing service internals over renaming public DTOs.
- Keep the frontend mock data shape aligned with backend DTOs while APIs remain stubbed.
- Preserve the product split: `Chat Workspace`, `Knowledge Base`, `Memory Studio`.

## Work On The Frontend

- Start with [`frontend/src/components/layout/AppShell.vue`](../../frontend/src/components/layout/AppShell.vue) and the relevant view in [`frontend/src/views`](../../frontend/src/views).
- Preserve the professional light workspace aesthetic:
  - deep blue-gray text
  - teal accent
  - large radii
  - soft glass cards
- Do not fall back to generic admin-table styling.
- Keep the debug panel vocabulary identical to backend payload keys.
- Update [`frontend/src/mocks/workspace.ts`](../../frontend/src/mocks/workspace.ts) when page structure or DTO shape changes.

## Work On The Backend

- Start with the blueprint in [`backend/app/api`](../../backend/app/api), then follow service, repo, and model boundaries.
- Keep `api -> service -> repo` direction strict.
- Put request and response shape changes in [`backend/app/models/schemas.py`](../../backend/app/models/schemas.py) first.
- Keep SSE event names stable: `token`, `tool_call`, `retrieval_debug`, `final_answer`, `error`.
- Treat the current service layer as scaffold code; replace mock internals without collapsing module boundaries.

## Work On RAG, Agent, And Memory

- Preserve the intended pipeline:
  - child chunk recall
  - parent chunk context recovery
  - vector + BM25 hybrid retrieval
  - RRF fusion
  - rerank
  - MMR + token budget truncation
- Keep tool inventory stable unless a new tool is clearly needed.
- Keep memory writes limited to durable user preferences, long-term tasks, stable facts, or explicit "remember this" instructions.
- Reflect behavior changes in [`docs/04-llm-rag-agent-guide.md`](../../docs/04-llm-rag-agent-guide.md).

## Validate Before Finishing

- Check whether the relevant docs file must change.
- Check whether frontend types, backend schemas, and mock data still agree.
- Run a lightweight syntax or import validation when tooling is available.
- Keep changes ASCII unless the file already contains Chinese or other Unicode text.
