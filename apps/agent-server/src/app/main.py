"""FastAPI entrypoint for the ADK logistics agent server."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.adk.runners import InMemoryRunner

from app.agents.root_agent import RootCoordinatorAgent
from app.api.routes import AppContainer, get_container, router
from app.mock_gateway.catalog import MockLogisticsGateway
from app.services.planner import DeterministicPlanner
from app.tools.logistics_tools import LogisticsToolRegistry


APP_NAME = "agents"


def create_app() -> FastAPI:
    """Create the backend app and wire all runtime dependencies."""

    gateway = MockLogisticsGateway()
    planner = DeterministicPlanner()
    tools = LogisticsToolRegistry(gateway=gateway)
    root_agent = RootCoordinatorAgent(planner=planner, tools=tools)
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    container = AppContainer(
        runner=runner,
        session_service=runner.session_service,
        app_name=APP_NAME,
    )

    app = FastAPI(title="ADK Logistics Agent Workbench", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.dependency_overrides[get_container] = lambda: container
    app.include_router(router)
    return app


app = create_app()
