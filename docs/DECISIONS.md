# Architectural Decision Records (ADRs)

Record significant technical decisions.

## Template
```
# ADR X: Title
Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded
Context:
Decision:
Consequences (Positive/Negative):
Related:
```

## Log
| ADR | Title | Date | Status |
|-----|-------|------|--------|
| 1 | Session-Scoped Conversation Manager | 2025-08-09 | Accepted |
| 2 | Optional LangChain Provider for LLM | 2025-08-09 | Accepted |

## ADR 1: Session-Scoped Conversation Manager
Date: 2025-08-09
Status: Accepted
Context:
- Need a layer between tools/validator and LLM to enforce session lifecycle and keep structured history.
Decision:
- Introduce `emotion_therapy.conversation` with `ConversationManager`, `LLMProvider` protocol, and `StubLLMProvider`.
- Persist structured turns on the `TherapySession.history` up to N turns.
Consequences:
- (+) Clear separation of concerns, easier testing, pluggable backends.
- (-) Slightly more complexity; requires updating tools to go through manager.
Related:
- PRD, TESTING_STRATEGY

## ADR 2: Optional LangChain Provider for LLM
Date: 2025-08-09
Status: Accepted
Context:
- Some deployments want advanced prompting/memory; others prefer deterministic stub.
Decision:
- Add `LangChainLLMProvider` behind env flag `THERAPY_USE_LANGCHAIN` and optional deps `extras=[langchain]`.
Consequences:
- (+) Flexible LLM backend; minimal impact if LC not installed.
- (-) Extra dependencies when enabled; requires OpenAI or similar credentials.
Related:
- conversation.py, tools wiring
