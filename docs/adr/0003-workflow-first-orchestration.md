# ADR 0003: Prefer Workflow-First Orchestration

## Status
Accepted

## Context
Logistics tasks such as tracking, pricing, and shipment creation have very different slot and validation requirements.

## Decision
Use one root coordinator plus multiple specialized workflow agents instead of a single monolithic agent implementation.

## Consequences
- Each workflow stays small and testable.
- Observability is clearer because trace steps align with business workflows.
- Frontend rendering becomes simpler because cards map cleanly to workflow output types.

