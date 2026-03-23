"""Simple trace recorder used to build frontend-visible execution steps."""

from __future__ import annotations

from app.domain.models import TraceKind, TraceStatus, TraceStep


class TraceRecorder:
    """Collects deterministic agent execution steps in display order."""

    def __init__(self) -> None:
        self._steps: list[TraceStep] = []

    def add(
        self,
        *,
        title: str,
        status: TraceStatus,
        summary: str,
        kind: TraceKind,
        data: dict | None = None,
    ) -> None:
        self._steps.append(
            TraceStep(
                title=title,
                status=status,
                summary=summary,
                kind=kind,
                data=data,
            )
        )

    @property
    def steps(self) -> list[TraceStep]:
        return list(self._steps)

