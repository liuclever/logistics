"""API routes for chat execution and trace lookup."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.domain.models import ConversationRequest, ConversationResponse, SessionTraceResponse, WorkspaceSessionState


class AppContainer:
    """Store the long-lived backend services needed by request handlers."""

    def __init__(self, *, runner: InMemoryRunner, session_service: InMemorySessionService, app_name: str) -> None:
        self.runner = runner
        self.session_service = session_service
        self.app_name = app_name
        self.user_id = "demo-user"


router = APIRouter()


def get_container() -> AppContainer:
    """Dependency placeholder overridden by the app factory."""

    raise RuntimeError("App container dependency has not been configured.")


@router.post("/api/chat", response_model=ConversationResponse)
async def chat(
    request: ConversationRequest,
    container: AppContainer = Depends(get_container),
) -> ConversationResponse:
    session_id = request.sessionId or str(uuid4())
    session = await container.session_service.get_session(
        app_name=container.app_name,
        user_id=container.user_id,
        session_id=session_id,
    )
    if session is None:
        await container.session_service.create_session(
            app_name=container.app_name,
            user_id=container.user_id,
            session_id=session_id,
            state={"workspace_state": WorkspaceSessionState().model_dump(mode="json")},
        )

    final_payload: dict | None = None
    user_message = types.Content(role="user", parts=[types.Part.from_text(text=request.message)])
    async for event in container.runner.run_async(
        user_id=container.user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.author == "LogisticsCoordinator":
            final_payload = event.custom_metadata or {}

    if final_payload is None:
        raise HTTPException(status_code=500, detail="Agent did not return a final payload.")
    return ConversationResponse.model_validate({"sessionId": session_id, **final_payload})


@router.get("/api/sessions/{session_id}/trace", response_model=SessionTraceResponse)
async def get_trace(
    session_id: str,
    container: AppContainer = Depends(get_container),
) -> SessionTraceResponse:
    session = await container.session_service.get_session(
        app_name=container.app_name,
        user_id=container.user_id,
        session_id=session_id,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    state = WorkspaceSessionState.model_validate(session.state.get("workspace_state", {}))
    return SessionTraceResponse(sessionId=session_id, traceSteps=state.last_trace, sessionState=state)

