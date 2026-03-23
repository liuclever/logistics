"""Deterministic workflow agents built on top of ADK BaseAgent."""

from __future__ import annotations

from typing import Any

from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event
from google.adk.events.event_actions import EventActions
from google.adk.runners import InvocationContext
from google.genai import types
from pydantic import PrivateAttr

from app.domain.models import (
    ActionMode,
    AgentAction,
    AgentPlan,
    PendingAction,
    ResponseCard,
    ShipmentDraft,
    ThinkingStep,
    WorkspaceSessionState,
)
from app.observability.trace import TraceRecorder
from app.services.planner import DeterministicPlanner
from app.tools.logistics_tools import LogisticsToolRegistry


WORKFLOW_PROMPTS = {
    "channelid": "还缺渠道信息。请告诉我使用哪个渠道，例如“香港TNT”或“美国快线”。",
    "customernumber1": "还缺客户参考号。请给我一个唯一的参考号，例如 `SZ-LA-1001`。",
    "number": "还缺总件数。请告诉我这票货有多少件。",
    "forecastweight": "还缺预报重量。请告诉我总重量，例如 `2.5kg`。",
    "countrycode": "还缺目的地国家。请告诉我是发往哪个国家。",
    "consigneename": "还缺收件人姓名。请告诉我收件人名称。",
    "consigneeaddress1": "还缺收件地址。请告诉我地址第一行。",
    "consigneecity": "还缺收件城市。请告诉我收件城市。",
    "consigneezipcode": "还缺邮编。请告诉我收件邮编。",
    "consigneeprovince": "还缺省州信息。请告诉我收件省州。",
    "origin_city": "还缺始发城市。请告诉我是从哪个城市发出。",
    "destination_countrycode": "还缺报价目的国。请告诉我要报价到哪个国家。",
    "weight": "还缺报价重量。请告诉我重量，例如 `3kg`。",
    "piece": "还缺报价件数。请告诉我件数。",
}


def build_action_card(*, title: str, summary: str, actions: list[AgentAction]) -> ResponseCard:
    """Build a normalized action list card for the workbench."""

    return ResponseCard(
        kind="action_list",
        title=title,
        data={
            "summary": summary,
            "actions": [action.model_dump(mode="json") for action in actions],
            "thinkingFlow": [step.model_dump(mode="json") for step in build_thinking_flow(summary=summary, actions=actions)],
        },
    )


def make_action(
    *,
    label: str,
    description: str,
    mode: ActionMode,
    tool: str | None = None,
    prompt: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AgentAction:
    """Create a compact operator-facing action item."""

    return AgentAction(
        label=label,
        description=description,
        mode=mode,
        tool=tool,
        prompt=prompt,
        payload=payload or {},
    )


def build_thinking_flow(*, summary: str, actions: list[AgentAction]) -> list[ThinkingStep]:
    """Generate a compact, frontend-safe reasoning summary for the action card."""

    primary_action = actions[0] if actions else None
    has_input_gap = any(action.mode == "input_required" for action in actions)
    has_confirmation = any(action.mode == "confirm_required" for action in actions)
    has_auto_action = any(action.mode == "auto" for action in actions)

    return [
        ThinkingStep(
            label="理解需求",
            title="先锁定本轮核心目标",
            content=summary,
        ),
        ThinkingStep(
            label="判断状态",
            title="确认当前是否可直接执行",
            content=(
                "当前仍有少量关键信息需要补齐，因此先给出低负担引导。"
                if has_input_gap
                else "当前已到确认边界，先等待用户确认再继续执行。"
                if has_confirmation
                else "当前参数已经具备执行条件，可以继续调用工具并整理结果。"
            ),
        ),
        ThinkingStep(
            label="选择动作",
            title=primary_action.label if primary_action else "等待下一步指令",
            content=(
                f"{primary_action.description}。"
                f"{' 将优先调用 ' + primary_action.tool if primary_action and primary_action.tool else ' 当前先通过对话推进。'}"
                if primary_action
                else "暂未识别到合适动作，等待用户提供更明确需求。"
            ),
        ),
        ThinkingStep(
            label="组织输出",
            title="把动作整理成低摩擦卡片",
            content=(
                "同时给出自动动作与可点击气泡，减少用户手动输入。"
                if has_auto_action
                else "输出结构化动作卡片，并保留必要的确认或补槽入口。"
            ),
        ),
    ]


class WorkflowAgent(BaseAgent):
    """Base class for every deterministic workflow agent."""

    _tools: LogisticsToolRegistry = PrivateAttr()

    def __init__(self, *, name: str, description: str, tools: LogisticsToolRegistry) -> None:
        super().__init__(name=name, description=description)
        self._tools = tools

    @property
    def tools(self) -> LogisticsToolRegistry:
        return self._tools

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def _run_async_impl(self, ctx: InvocationContext):
        # This path is only for debugging a workflow agent directly.
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=f"{self.name} is a delegated workflow agent.")],
            ),
            turn_complete=True,
            actions=EventActions(end_of_agent=True),
        )


class ReferenceResolutionWorkflow(WorkflowAgent):
    """Resolve any visible user number into a canonical tracking target."""

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        reference = str(plan.extracted_entities.get("reference_number", "")).replace("#", "")
        if not reference:
            trace.add(
                title="缺少单号",
                status="warning",
                summary="用户没有提供可追踪的编号。",
                kind="validation",
            )
            return {
                "reply": "我还没拿到可追踪的单号。你可以直接发客户参考号、系统单号或运单号。",
                "cards": [
                    build_action_card(
                        title="建议动作",
                        summary="先补一个可追踪编号，或者先浏览最近订单。",
                        actions=[
                            make_action(
                                label="输入运单号",
                                description="直接输入客户参考号、系统单号或运单号。",
                                mode="input_required",
                                tool="resolve_waybill_number",
                                prompt="查询订单 #12345 的运输状态",
                            ),
                            make_action(
                                label="浏览最近订单",
                                description="先看最近订单列表，再复制编号继续查询。",
                                mode="navigation",
                                tool="list_orders",
                                prompt="查询订单",
                            ),
                        ],
                    )
                ],
                "pending_action": None,
                "state": state,
            }

        trace.add(
            title="解析单号类型",
            status="completed",
            summary=f"识别到用户编号 `{reference}`，先做单号归一化解析。",
            kind="decision",
        )
        resolved = self.tools.unwrap(self.tools.resolve_waybill_number(reference))
        trace.add(
            title="调用 resolve_waybill_number",
            status="completed" if resolved.success else "failed",
            summary=resolved.msg,
            kind="tool",
            data={"search_number": reference, "result": resolved.model_dump(mode="json")},
        )
        if not resolved.success or not resolved.data:
            return {
                "reply": f"我查过了，当前找不到 `{reference}` 对应的运单。你可以换客户参考号、系统单号或运单号再试。",
                "cards": [
                    ResponseCard(
                        kind="error",
                        title="单号解析失败",
                        data={"searchNumber": reference, "message": resolved.msg},
                    ),
                    build_action_card(
                        title="下一步动作",
                        summary="可以更换编号重试，或者先浏览最近订单。",
                        actions=[
                            make_action(
                                label="更换单号重试",
                                description="换客户参考号、系统单号或运单号再解析一次。",
                                mode="input_required",
                                tool="resolve_waybill_number",
                            ),
                            make_action(
                                label="浏览最近订单",
                                description="先看最近订单列表，确认正确编号。",
                                mode="navigation",
                                tool="list_orders",
                                prompt="查询订单",
                            ),
                        ],
                    ),
                ],
                "pending_action": None,
                "state": state,
            }

        tracker = TrackShipmentWorkflow(
            name="TrackShipmentWorkflow",
            description="Track shipment status",
            tools=self.tools,
        )
        tracking_plan = plan.model_copy(
            update={
                "intent": "track_shipment",
                "selected_workflow": "TrackShipmentWorkflow",
                "extracted_entities": {
                    **plan.extracted_entities,
                    "reference_number": resolved.data["waybillnumber"],
                },
            }
        )
        return await tracker.execute(ctx=ctx, plan=tracking_plan, state=state, planner=planner, trace=trace)


class TrackShipmentWorkflow(WorkflowAgent):
    """Handle shipment tracking queries."""

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        reference = str(plan.extracted_entities.get("reference_number", "")).replace("#", "")
        tracked = self.tools.unwrap(self.tools.track_order(reference))
        trace.add(
            title="调用 track_order",
            status="completed" if tracked.success else "failed",
            summary=tracked.msg,
            kind="tool",
            data={"search_number": reference, "result": tracked.model_dump(mode="json")},
        )
        state.stats.tracking_queries += 1
        if not tracked.success or not tracked.data:
            return {
                "reply": f"我暂时没查到 `{reference}` 的轨迹信息。建议再核对一下编号。",
                "cards": [
                    ResponseCard(
                        kind="error",
                        title="轨迹查询失败",
                        data={"searchNumber": reference, "message": tracked.msg},
                    ),
                    build_action_card(
                        title="建议动作",
                        summary="可以重新输入编号，或者先查看最近订单。",
                        actions=[
                            make_action(
                                label="重新输入编号",
                                description="更换编号后再次调用轨迹工具。",
                                mode="input_required",
                                tool="track_order",
                            ),
                            make_action(
                                label="查看最近订单",
                                description="浏览最近订单，定位可用编号。",
                                mode="navigation",
                                tool="list_orders",
                                prompt="查询订单",
                            ),
                        ],
                    ),
                ],
                "pending_action": None,
                "state": state,
            }

        row = tracked.data[0]
        latest = row["trackItems"][0]
        return {
            "reply": (
                f"运单 `{row['waybillnumber']}` 当前状态是 **{row['orderstatusName']}**。"
                f" 最新节点：{latest['trackdate_utc8']}，{latest['location']}，{latest['info']}。"
            ),
            "cards": [
                ResponseCard(
                    kind="shipment_summary",
                    title="运单摘要",
                    data={
                        "systemnumber": row["systemnumber"],
                        "waybillnumber": row["waybillnumber"],
                        "tracknumber": row["tracknumber"],
                        "countrycode": row["countrycode"],
                        "status": row["orderstatusName"],
                    },
                ),
                ResponseCard(
                    kind="track_timeline",
                    title="运输轨迹",
                    data={
                        "searchNumber": row["searchNumber"],
                        "status": row["orderstatusName"],
                        "trackItems": row["trackItems"],
                    },
                ),
                build_action_card(
                    title="可执行动作",
                    summary="你可以继续追踪别的单号，或转入订单浏览。",
                    actions=[
                        make_action(
                            label="追踪其他订单",
                            description="继续输入新的编号并调用轨迹工具。",
                            mode="input_required",
                            tool="track_order",
                            prompt="查询订单 #12345 的运输状态",
                        ),
                        make_action(
                            label="浏览最近订单",
                            description="查看最近订单摘要和编号。",
                            mode="navigation",
                            tool="list_orders",
                            prompt="查询订单",
                        ),
                    ],
                ),
            ],
            "pending_action": None,
            "state": state,
        }


class QuoteWorkflow(WorkflowAgent):
    """Handle shipment pricing with multi-turn slot filling."""

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        state.quote_draft = planner.merge_quote_draft(
            existing=state.quote_draft,
            extracted=plan.extracted_entities,
        )
        missing = planner.quote_missing_slots(state.quote_draft)
        trace.add(
            title="校验报价槽位",
            status="completed" if not missing else "warning",
            summary="报价信息校验完成。" if not missing else f"仍缺少 {len(missing)} 个必填字段。",
            kind="validation",
            data={"missing_slots": missing, "draft": state.quote_draft.model_dump(mode="json")},
        )
        if missing:
            return {
                "reply": WORKFLOW_PROMPTS[missing[0]],
                "cards": [
                    build_action_card(
                        title="建议动作",
                        summary="当前报价还不能执行，先补齐必要字段或浏览支持信息。",
                        actions=[
                            make_action(
                                label="补当前字段",
                                description=f"优先补 `{missing[0]}`，继续完成报价。",
                                mode="input_required",
                                tool="search_price",
                            ),
                            make_action(
                                label="浏览渠道",
                                description="先看支持渠道，再决定是否指定渠道报价。",
                                mode="auto",
                                tool="list_channels",
                                prompt="查看渠道列表",
                            ),
                            make_action(
                                label="浏览目的地",
                                description="查看支持报价的国家目录。",
                                mode="auto",
                                tool="list_destinations",
                                prompt="查看支持目的地",
                            ),
                        ],
                    )
                ],
                "pending_action": None,
                "state": state,
            }

        priced = self.tools.unwrap(
            self.tools.search_price(
                destination_countrycode=state.quote_draft.destination_countrycode or "",
                destination_city=state.quote_draft.destination_city,
                weight=float(state.quote_draft.weight or 0),
                piece=int(state.quote_draft.piece or 0),
                channelid=state.quote_draft.channelid,
            )
        )
        trace.add(
            title="调用 search_price",
            status="completed" if priced.success else "failed",
            summary=priced.msg,
            kind="tool",
            data=priced.model_dump(mode="json"),
        )
        state.stats.quote_queries += 1
        if not priced.success or not priced.data:
            return {
                "reply": f"这次报价没成功，原因是：{priced.msg}",
                "cards": [
                    ResponseCard(kind="error", title="报价失败", data={"message": priced.msg}),
                    build_action_card(
                        title="下一步动作",
                        summary="你可以修正参数后重试，或浏览支持渠道与目的地。",
                        actions=[
                            make_action(
                                label="修正后重试",
                                description="补充正确重量、件数或目的地后再次报价。",
                                mode="input_required",
                                tool="search_price",
                            ),
                            make_action(
                                label="浏览渠道",
                                description="查看支持的渠道与命名。",
                                mode="auto",
                                tool="list_channels",
                                prompt="查看渠道列表",
                            ),
                        ],
                    ),
                ],
                "pending_action": None,
                "state": state,
            }

        state.quote_draft = None
        return {
            "reply": "我已经完成试算，结果里可以直接比较渠道、时效和总金额。",
            "cards": [
                ResponseCard(
                    kind="price_table",
                    title="报价结果",
                    data={"rows": [self._normalize_price_row(row) for row in priced.data]},
                ),
                build_action_card(
                    title="可执行动作",
                    summary="报价已经出来了，你可以继续比渠道，或转入建单流程。",
                    actions=[
                        make_action(
                            label="切换为建单",
                            description="沿用当前目的地信息，直接开始创建货运单。",
                            mode="input_required",
                            tool="create_order",
                            prompt="创建从深圳到洛杉矶的新货运单",
                        ),
                        make_action(
                            label="重新报价",
                            description="修改重量、件数或渠道后重新试算。",
                            mode="input_required",
                            tool="search_price",
                            prompt="先查一下美国报价 5kg 2件",
                        ),
                        make_action(
                            label="浏览渠道列表",
                            description="查看全部渠道，再决定是否指定渠道。",
                            mode="auto",
                            tool="list_channels",
                            prompt="查看渠道列表",
                        ),
                    ],
                ),
            ],
            "pending_action": None,
            "state": state,
        }

    def _normalize_price_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Shape quote rows to the frontend contract while preserving source fields."""

        total_cost = row.get("total_cost", row.get("totalcost", row.get("totalCost")))
        currency = row.get("currency", row.get("totalCostCcy"))
        channel = row.get("channel", row.get("channelname"))
        return {
            **row,
            "channel": channel,
            "channelname": row.get("channelname", channel),
            "aging": row.get("aging"),
            "total_cost": total_cost,
            "totalcost": total_cost,
            "currency": currency,
            "note": row.get("note"),
        }


class OrderLookupWorkflow(WorkflowAgent):
    """Handle simple recent-order listing."""

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        listed = self.tools.unwrap(self.tools.list_orders())
        trace.add(
            title="调用 list_orders",
            status="completed" if listed.success else "failed",
            summary=listed.msg,
            kind="tool",
            data=listed.model_dump(mode="json"),
        )
        if not listed.success or not listed.data:
            return {
                "reply": "订单查询接口现在没有返回有效数据。",
                "cards": [
                    ResponseCard(kind="error", title="订单查询失败", data={"message": listed.msg}),
                    build_action_card(
                        title="建议动作",
                        summary="你可以稍后重试，或者直接输入明确单号查轨迹。",
                        actions=[
                            make_action(
                                label="直接查轨迹",
                                description="输入明确编号，直接走轨迹工作流。",
                                mode="input_required",
                                tool="track_order",
                                prompt="查询订单 #12345 的运输状态",
                            ),
                            make_action(
                                label="重新查询订单",
                                description="稍后重新调用订单列表工具。",
                                mode="auto",
                                tool="list_orders",
                                prompt="查询订单",
                            ),
                        ],
                    ),
                ],
                "pending_action": None,
                "state": state,
            }

        return {
            "reply": f"我找到了 {min(len(listed.data), 5)} 条最近订单，已经整理到结果卡片里。",
            "cards": [
                ResponseCard(kind="stats", title="最近订单", data={"rows": listed.data[:5]}),
                build_action_card(
                    title="可执行动作",
                    summary="你可以从订单列表继续追踪轨迹，或开启新建单流程。",
                    actions=[
                        make_action(
                            label="继续查轨迹",
                            description="复制一个订单编号后继续查运输状态。",
                            mode="input_required",
                            tool="track_order",
                            prompt="查询订单 #12345 的运输状态",
                        ),
                        make_action(
                            label="开始建单",
                            description="创建新的货运单并进入补槽流程。",
                            mode="input_required",
                            tool="create_order",
                            prompt="创建从深圳到洛杉矶的新货运单",
                        ),
                    ],
                ),
            ],
            "pending_action": None,
            "state": state,
        }


class CreateShipmentWorkflow(WorkflowAgent):
    """Handle create-order flows, slot filling, and final confirmation."""

    async def execute(
        self,
        *,
        ctx: InvocationContext,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        if state.pending_action:
            return self._handle_confirmation(plan=plan, state=state, planner=planner, trace=trace)

        state.shipment_draft = planner.merge_shipment_draft(
            existing=state.shipment_draft,
            extracted=plan.extracted_entities,
            source_message=plan.user_message,
        )
        missing = planner.shipment_missing_slots(state.shipment_draft)
        trace.add(
            title="校验建单槽位",
            status="completed" if not missing else "warning",
            summary="建单字段校验完成。" if not missing else f"仍缺少 {len(missing)} 个关键字段。",
            kind="validation",
            data={"missing_slots": missing, "draft": state.shipment_draft.model_dump(mode="json")},
        )
        if missing:
            return {
                "reply": WORKFLOW_PROMPTS[missing[0]],
                "cards": [
                    build_action_card(
                        title="建议动作",
                        summary="当前建单信息还不完整，先补关键字段或浏览支持渠道。",
                        actions=[
                            make_action(
                                label="补当前字段",
                                description=f"优先补 `{missing[0]}`，继续完成建单。",
                                mode="input_required",
                                tool="create_order",
                            ),
                            make_action(
                                label="浏览渠道",
                                description="先看渠道列表，再决定用哪个渠道创建货运单。",
                                mode="auto",
                                tool="list_channels",
                                prompt="查看渠道列表",
                            ),
                            make_action(
                                label="切到报价流程",
                                description="如果还没决定渠道和重量，可以先查报价。",
                                mode="navigation",
                                tool="search_price",
                                prompt="先查一下美国报价 3kg 1件",
                            ),
                        ],
                    )
                ],
                "pending_action": None,
                "state": state,
            }

        pending = PendingAction(
            kind="confirm_create_order",
            summary="已收齐建单信息，等待你确认后正式模拟下单。",
            payload=state.shipment_draft.model_dump(mode="json"),
        )
        state.pending_action = pending
        return {
            "reply": "建单信息已经整理好了。你确认的话，直接回复“确认”即可；如果想取消，回复“取消”。",
            "cards": [
                ResponseCard(
                    kind="confirmation",
                    title="待确认建单摘要",
                    data={
                        "summary": pending.summary,
                        "draft": state.shipment_draft.model_dump(mode="json"),
                        "actionId": pending.action_id,
                    },
                ),
                build_action_card(
                    title="确认前动作",
                    summary="你可以直接确认提交，也可以取消本次建单。",
                    actions=[
                        make_action(
                            label="确认提交",
                            description="调用模拟建单工具生成系统单号与运单号。",
                            mode="confirm_required",
                            tool="create_order",
                            prompt="确认",
                        ),
                        make_action(
                            label="取消建单",
                            description="终止当前建单流程并清空草稿。",
                            mode="confirm_required",
                            prompt="取消",
                        ),
                    ],
                ),
            ],
            "pending_action": pending,
            "state": state,
        }

    def _handle_confirmation(
        self,
        *,
        plan: AgentPlan,
        state: WorkspaceSessionState,
        planner: DeterministicPlanner,
        trace: TraceRecorder,
    ) -> dict[str, Any]:
        message = plan.user_message
        if planner.is_negative_confirmation(message):
            trace.add(
                title="用户取消建单",
                status="warning",
                summary="用户在确认环节取消了创建运单。",
                kind="decision",
            )
            state.pending_action = None
            state.shipment_draft = None
            return {
                "reply": "好的，这次建单我已经取消。需要重新创建时直接告诉我即可。",
                "cards": [
                    build_action_card(
                        title="下一步动作",
                        summary="你可以重新发起建单，或者先查报价。",
                        actions=[
                            make_action(
                                label="重新建单",
                                description="重新进入建单补槽流程。",
                                mode="input_required",
                                tool="create_order",
                                prompt="创建从深圳到洛杉矶的新货运单",
                            ),
                            make_action(
                                label="先查报价",
                                description="先做渠道和费用试算，再决定是否下单。",
                                mode="input_required",
                                tool="search_price",
                                prompt="先查一下美国报价 3kg 1件",
                            ),
                        ],
                    )
                ],
                "pending_action": None,
                "state": state,
            }
        if not planner.is_positive_confirmation(message):
            return {
                "reply": "当前这一步需要明确确认。回复“确认”我就提交模拟建单，回复“取消”我就终止本次流程。",
                "cards": [
                    build_action_card(
                        title="待确认动作",
                        summary="这一步只接受确认或取消两种动作。",
                        actions=[
                            make_action(
                                label="确认提交",
                                description="正式调用模拟建单工具。",
                                mode="confirm_required",
                                tool="create_order",
                                prompt="确认",
                            ),
                            make_action(
                                label="取消建单",
                                description="终止当前建单流程。",
                                mode="confirm_required",
                                prompt="取消",
                            ),
                        ],
                    )
                ],
                "pending_action": state.pending_action,
                "state": state,
            }

        draft = state.shipment_draft or ShipmentDraft()
        result = self.tools.unwrap(self.tools.create_order(draft.model_dump(mode="json")))
        trace.add(
            title="调用 create_order",
            status="completed" if result.success else "failed",
            summary=result.msg,
            kind="tool",
            data=result.model_dump(mode="json"),
        )
        state.pending_action = None
        if not result.success or not result.data:
            state.stats.failed_orders += 1
            return {
                "reply": f"模拟建单失败，原因是：{result.msg}",
                "cards": [
                    ResponseCard(kind="error", title="建单失败", data={"message": result.msg}),
                    build_action_card(
                        title="下一步动作",
                        summary="你可以修正参数后重试，或先切到报价流程。",
                        actions=[
                            make_action(
                                label="重新建单",
                                description="修正参考号或收件信息后再次创建。",
                                mode="input_required",
                                tool="create_order",
                            ),
                            make_action(
                                label="先查报价",
                                description="先确认费用和渠道，再决定是否创建。",
                                mode="input_required",
                                tool="search_price",
                                prompt="先查一下美国报价 3kg 1件",
                            ),
                        ],
                    ),
                ],
                "pending_action": None,
                "state": state,
            }

        state.stats.successful_orders += 1
        state.shipment_draft = None
        row = result.data[0]
        return {
            "reply": f"模拟建单已经完成，系统单号 `{row['systemnumber']}`，运单号 `{row['waybillnumber']}`。",
            "cards": [
                ResponseCard(kind="shipment_summary", title="建单结果", data=row),
                build_action_card(
                    title="可执行动作",
                    summary="你可以继续查轨迹、再创建一票，或浏览最近订单。",
                    actions=[
                        make_action(
                            label="查询新单轨迹",
                            description="使用新生成的运单号继续查询轨迹。",
                            mode="input_required",
                            tool="track_order",
                            prompt=f"查询订单 {row['waybillnumber']} 的运输状态",
                        ),
                        make_action(
                            label="再创建一票",
                            description="继续发起下一票货运单创建。",
                            mode="input_required",
                            tool="create_order",
                            prompt="创建从深圳到洛杉矶的新货运单",
                        ),
                        make_action(
                            label="浏览最近订单",
                            description="查看最近订单列表和编号。",
                            mode="navigation",
                            tool="list_orders",
                            prompt="查询订单",
                        ),
                    ],
                ),
            ],
            "pending_action": None,
            "state": state,
        }
