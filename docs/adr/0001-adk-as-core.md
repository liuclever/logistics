# ADR 0001: Use Google ADK As The Core Agent Framework

## Status
Accepted

## Context
The task explicitly requires Google ADK. A different primary framework would weaken compliance with the assignment.

## Decision
Use Google ADK as the core runtime and agent abstraction layer.

## Consequences
- ADK primitives remain visible in the implementation.
- The system can be explained clearly during review as an ADK-based agent system.
- Graph-style workflow thinking can still be applied without replacing ADK.

