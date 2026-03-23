"""Root ADK agent that orchestrates deterministic logistics workflows."""

from __future__ import annotations

from typing import Any

from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.runners import InvocationContext
from google.genai import types
from pydantic import PrivateAttr

from app.agents.workflows import (
    CreateShipmentWorkflow,
    OrderLookupWorkflow,
    QuoteWorkflow,
    ReferenceResolutionWorkflow,
)
from app.domain.models import AgentPlan, ResponseCard, WorkspaceSessionState
from app.observability.trace import TraceRecorder
from app.services.planner import DeterministicPlanner
from app.tools.logistics_tools import LogisticsToolRegistry


class RootCoordinatorAgent(BaseAgent):
    """Top-level deterministic coordinator backed by ADK runtime primitives."""

    _planner: DeterministicPlanner = PrivateAttr()
    _tools: LogisticsToolRegistry = PrivateAttr()
    _reference_resolution: ReferenceResolutionWorkflow = PrivateAttr()
    _create_workflow: CreateShipmentWorkflow = PrivateAttr()
    _quote_workflow: QuoteWorkflow = PrivateAttr()
    _lookup_workflow: OrderLookupWorkflow = PrivateAttr()

    def __init__(self, *, planner: DeterministicPlanner, tools: LogisticsToolRegistry) -> None:
        reference_resolution = ReferenceResolutionWorkflow(
            name="ReferenceResolutionWorkflow",
            description="Resolve order references before tracking",
            tools=tools,
        )
        create_workflow = CreateShipmentWorkflow(
            name="CreateShipmentWorkflow",
            description="Create shipment drafts with confirmation",
            tools=tools,
        )
        quote_workflow = QuoteWorkflow(
            name="QuoteWorkflow",
            description="Price shipment requests",
            tools=tools,
        )
        lookup_workflow = OrderLookupWorkflow(
            name="OrderLookupWorkflow",
            description="List recent orders",
            tools=tools,
        )
        super().__init__(
            name="LogisticsCoordinator",
            description="Offline logistics workbench coordinator powered by Google ADK",
            sub_agents=[
                reference_resolution,
                create_workflow,
                quote_workflow,
                lookup_workflow,
            ],
        )
        self._planner = planner
        self._tools = tools
        self._reference_resolution = reference_resolution
        self._create_workflow = create_workflow
        self._quote_workflow = quote_workflow
        self._lookup_workflow = lookup_workflow

    @property
    def planner(self) -> DeterministicPlanner:
        return self._planner

    @property
    def tools(self) -> LogisticsToolRegistry:
        return self._tools

    @property
    def reference_resolution(self) -> ReferenceResolutionWorkflow:
        return self._reference_resolution

    @property
    def create_workflow(self) -> CreateShipmentWorkflow:
        return self._create_workflow

    @property
    def quote_workflow(self) -> QuoteWorkflow:
        return self._quote_workflow

    @property
    def lookup_workflow(self) -> OrderLookupWorkflow:
        return self._lookup_workflow

    async def _run_async_impl(self, ctx: InvocationContext):
        """Plan the user request, dispatch one workflow, and emit one final ADK event."""

        message = self._extract_user_message(ctx)
        state = self._load_state(ctx)
        state.stats.total_messages += 1
        trace = TraceRecorder()

        plan = self.planner.plan(message, state)
        trace.add(
            title="意图识别",
            status="completed",
            summary=f"识别意图为 `{plan.intent}`，工作流 `{plan.selected_workflow}`。",
            kind="decision",
            data=plan.model_dump(mode="json"),
        )

        result = await self._dispatch(ctx=ctx, plan=plan, state=state, trace=trace)
        result_state = result["state"]
        result_state.last_plan = plan
        result_state.last_cards = result["cards"]
        trace.add(
            title="结果汇总",
            status="completed",
            summary="本轮执行已经整理为前端可消费的结构化响应。",
            kind="summary",
            data={"card_count": len(result["cards"])},
        )
        result_state.last_trace = trace.steps

        payload = {
            "reply": result["reply"],
            "traceSteps": [step.model_dump(mode="json") for step in trace.steps],
            "cards": [card.model_dump(mode="json") for card in result["cards"]],
            "pendingAction": result["pending_action"].model_dump(mode="json") if result["pending_action"] else None,
            "sessionState": result_state.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
        }
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=result["reply"])],
            ),
            turn_complete=True,
            custom_metadata=payload,
            actions=EventActions(
                state_delta={"workspace_state": result_state.model_dump(mode="json")},
                end_of_agent=True,
            ),
        )

    async def _dispatch(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        if plan.selected_workflow == "ReferenceResolutionWorkflow":
            return await self.reference_resolution.execute(
                ctx=ctx,
                plan=plan,
                state=state,
                planner=self.planner,
                trace=trace,
            )
        if plan.selected_workflow == "CreateShipmentWorkflow":
            return await self.create_workflow.execute(
                ctx=ctx,
                plan=plan,
                state=state,
                planner=self.planner,
                trace=trace,
            )
        if plan.selected_workflow == "QuoteWorkflow":
            return await self.quote_workflow.execute(
                ctx=ctx,
                plan=plan,
                state=state,
                planner=self.planner,
                trace=trace,
            )
        if plan.selected_workflow == "OrderLookupWorkflow":
            return await self.lookup_workflow.execute(
                ctx=ctx,
                plan=plan,
                state=state,
                planner=self.planner,
                trace=trace,
            )
        return {
            "reply": (
                "我目前支持三类高价值动作：查轨迹、查报价、创建货运单。"
                " 你可以试试“查询订单 #12345 的运输状态”或“创建从深圳到洛杉矶的新货运单”。"
            ),
            "cards": [
                ResponseCard(
                    kind="stats",
                    title="可执行任务",
                    data={
                        "examples": [
                            "查询订单 #12345 的运输状态",
                            "帮我从深圳发一票货到洛杉矶",
                            "先查一下美国报价",
                        ]
                    },
                )
            ],
            "pending_action": None,
            "state": state,
        }

    def _extract_user_message(self, ctx: InvocationContext) -> str:
        """Extract plain text from the ADK input content object."""

        if not ctx.user_content or not ctx.user_content.parts:
            return ""
        texts = [part.text for part in ctx.user_content.parts if part.text]
        return "\n".join(texts).strip()

    def _load_state(self, ctx: InvocationContext) -> WorkspaceSessionState:
        """Rehydrate session state from the ADK session store."""

        raw_state = ctx.session.state.get("workspace_state")
        if not raw_state:
            return WorkspaceSessionState()
        return WorkspaceSessionState.model_validate(raw_state)
