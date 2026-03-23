# ADR 0002: Use An Offline Deterministic Planner

## Status
Accepted

## Context
The project must be demonstrable without real logistics credentials, and the current preferred delivery mode is offline demo.

## Decision
Use a deterministic planner with regex, keyword routing, session-state-aware slot filling, and explicit confirmation logic.

## Consequences
- Demo reliability is high.
- The backend remains testable without external dependencies.
- Real model integration can be introduced later behind the same workflow contracts.

