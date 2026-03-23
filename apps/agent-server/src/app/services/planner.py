"""Deterministic planner used by the offline ADK logistics agent."""

from __future__ import annotations

import re
from typing import Any

from app.domain.models import AgentAction, AgentPlan, IntentName, QuoteDraft, ShipmentDraft, WorkspaceSessionState
from app.mock_gateway.catalog import CHANNELS, CITY_DIRECTORY


YES_WORDS = {"确认", "好的", "ok", "yes", "y", "确认下单", "提交"}
NO_WORDS = {"取消", "不用了", "no", "n", "拒绝", "先不创建"}
GREETING_WORDS = {
    "你好",
    "您好",
    "hi",
    "hello",
    "hey",
    "在吗",
    "在不在",
}
COUNTRY_ALIASES = {
    "美国": "US",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "中国": "CN",
    "cn": "CN",
    "china": "CN",
    "英国": "GB",
    "uk": "GB",
    "gb": "GB",
    "united kingdom": "GB",
}


class DeterministicPlanner:
    """Rule-based planner that emulates enterprise workflow routing."""

    def plan(self, message: str, session_state: WorkspaceSessionState) -> AgentPlan:
        normalized = message.strip()
        lowered = normalized.lower()
        extracted = self.extract_entities(normalized)
        has_explicit_intent = self._has_explicit_intent_keyword(lowered)

        if not normalized:
            return self._build_plan(
                intent="unknown",
                selected_workflow="UnknownWorkflow",
                confidence=0.2,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if lowered in GREETING_WORDS:
            return self._build_plan(
                intent="greeting",
                selected_workflow="UnknownWorkflow",
                confidence=0.95,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if session_state.pending_action:
            intent: IntentName = "confirm_action"
            return self._build_plan(
                intent=intent,
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.99,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if session_state.quote_draft and re.fullmatch(r"\d+", lowered):
            extracted.setdefault("piece", int(lowered))

        if session_state.shipment_draft and self._looks_like_slot_answer(lowered) and not has_explicit_intent:
            return self._build_plan(
                intent="provide_missing",
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.93,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if session_state.quote_draft and self._looks_like_slot_answer(lowered) and not has_explicit_intent:
            return self._build_plan(
                intent="provide_missing",
                selected_workflow="QuoteWorkflow",
                confidence=0.93,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if any(keyword in lowered for keyword in ["查价", "报价", "price", "quote"]):
            return self._build_plan(
                intent="quote_shipment",
                selected_workflow="QuoteWorkflow",
                confidence=0.95,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if any(keyword in lowered for keyword in ["创建", "下单", "货运单", "发一票", "建单"]):
            return self._build_plan(
                intent="create_shipment",
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.97,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if any(keyword in lowered for keyword in ["运输状态", "轨迹", "track", "物流状态"]):
            return self._build_plan(
                intent="track_shipment",
                selected_workflow="ReferenceResolutionWorkflow",
                confidence=0.95,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        if any(keyword in lowered for keyword in ["订单列表", "订单查询", "分页查询", "最近订单", "查询订单"]):
            if "reference_number" in extracted:
                return self._build_plan(
                    intent="track_shipment",
                    selected_workflow="ReferenceResolutionWorkflow",
                    confidence=0.93,
                    extracted_entities=extracted,
                    user_message=normalized,
                    session_state=session_state,
                )
            return self._build_plan(
                intent="order_lookup",
                selected_workflow="OrderLookupWorkflow",
                confidence=0.88,
                extracted_entities=extracted,
                user_message=normalized,
                session_state=session_state,
            )

        return self._build_plan(
            intent="unknown",
            selected_workflow="UnknownWorkflow",
            confidence=0.4,
            extracted_entities=extracted,
            user_message=normalized,
            session_state=session_state,
        )

    def extract_entities(self, message: str) -> dict[str, Any]:
        """Extracts the small set of entities needed by the workflows."""

        lowered = message.lower()
        extracted: dict[str, Any] = {}

        reference_match = re.search(r"#?([A-Za-z0-9-]{4,})", message)
        if reference_match:
            extracted["reference_number"] = reference_match.group(1)

        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|公斤)", lowered)
        if weight_match:
            extracted["forecastweight"] = float(weight_match.group(1))
            extracted["weight"] = float(weight_match.group(1))

        piece_match = re.search(r"(\d+)\s*(?:件|箱|票)", lowered)
        if piece_match:
            extracted["number"] = int(piece_match.group(1))
            extracted["piece"] = int(piece_match.group(1))

        for channel in CHANNELS:
            names = {
                str(channel["channelid"]).lower(),
                str(channel["channelname"]).lower(),
                str(channel["channelnamecn"]).lower(),
            }
            if any(name in lowered for name in names):
                extracted["channelid"] = channel["channelid"]
                extracted["channelname"] = channel["channelname"]
                break

        route_match = re.search(r"从(.+?)到(.+?)(?:的新|的货运单|下单|$)", message)
        if route_match:
            extracted["origin_city"] = route_match.group(1).strip()
            extracted["destination_city"] = route_match.group(2).strip()

        consignee_match = re.search(r"收件人[:： ]*([A-Za-z\u4e00-\u9fa5 ]+)", message)
        if consignee_match:
            extracted["consigneename"] = consignee_match.group(1).strip()

        address_match = re.search(r"地址[:： ]*([A-Za-z0-9\u4e00-\u9fa5 #,.-]+)", message)
        if address_match:
            extracted["consigneeaddress1"] = address_match.group(1).strip()

        ref_match = re.search(r"(?:参考号|订单号|客户单号)[:： ]*([A-Za-z0-9-]+)", message)
        if ref_match:
            extracted["customernumber1"] = ref_match.group(1).strip()

        for alias, code in COUNTRY_ALIASES.items():
            if alias in lowered:
                extracted.setdefault("destination_countrycode", code)
                extracted.setdefault("countrycode", code)
                break

        self._hydrate_city_defaults(extracted)
        return extracted

    def merge_shipment_draft(
        self,
        *,
        existing: ShipmentDraft | None,
        extracted: dict[str, Any],
        source_message: str,
    ) -> ShipmentDraft:
        """Merges newly extracted fields into the existing shipment draft."""

        draft = existing.model_copy(deep=True) if existing else ShipmentDraft()
        for key, value in extracted.items():
            if hasattr(draft, key):
                setattr(draft, key, value)
        draft.source_message = source_message
        return draft

    def merge_quote_draft(
        self,
        *,
        existing: QuoteDraft | None,
        extracted: dict[str, Any],
    ) -> QuoteDraft:
        """Merges quote slots across turns."""

        draft = existing.model_copy(deep=True) if existing else QuoteDraft()
        mapping = {
            "destination_countrycode": "destination_countrycode",
            "destination_city": "destination_city",
            "weight": "weight",
            "piece": "piece",
            "channelid": "channelid",
        }
        for source_key, target_key in mapping.items():
            if source_key in extracted:
                setattr(draft, target_key, extracted[source_key])
        return draft

    def shipment_missing_slots(self, draft: ShipmentDraft) -> list[str]:
        """Returns shipment slots still required for a safe create-order flow."""

        required = [
            "channelid",
            "customernumber1",
            "number",
            "forecastweight",
            "countrycode",
            "consigneename",
            "consigneeaddress1",
            "consigneecity",
            "consigneezipcode",
            "consigneeprovince",
            "origin_city",
        ]
        return [field for field in required if getattr(draft, field) in (None, "", 0)]

    def quote_missing_slots(self, draft: QuoteDraft) -> list[str]:
        """Returns quote slots that must be present before pricing."""

        required = ["destination_countrycode", "weight", "piece"]
        return [field for field in required if getattr(draft, field) in (None, "", 0)]

    def is_positive_confirmation(self, message: str) -> bool:
        return message.strip().lower() in YES_WORDS

    def is_negative_confirmation(self, message: str) -> bool:
        return message.strip().lower() in NO_WORDS

    def _looks_like_slot_answer(self, lowered: str) -> bool:
        return bool(re.fullmatch(r"\d+", lowered)) or any(
            token in lowered
            for token in ["渠道", "参考号", "收件人", "地址", "kg", "公斤", "件", "从", "到"]
        )

    def _has_explicit_intent_keyword(self, lowered: str) -> bool:
        return any(
            keyword in lowered
            for keyword in [
                "查价",
                "报价",
                "price",
                "quote",
                "创建",
                "下单",
                "货运单",
                "发一票",
                "建单",
                "运输状态",
                "轨迹",
                "track",
                "物流状态",
                "订单列表",
                "订单查询",
                "分页查询",
                "最近订单",
                "查询订单",
            ]
        )

    def _build_plan(
        self,
        *,
        intent: IntentName,
        selected_workflow: str,
        confidence: float,
        extracted_entities: dict[str, Any],
        user_message: str,
        session_state: WorkspaceSessionState,
    ) -> AgentPlan:
        """Create a plan object with candidate actions attached for the workbench."""

        return AgentPlan(
            intent=intent,
            selected_workflow=selected_workflow,
            confidence=confidence,
            extracted_entities=extracted_entities,
            missing_slots=[],
            candidate_actions=self._build_candidate_actions(
                intent=intent,
                extracted_entities=extracted_entities,
                session_state=session_state,
            ),
            user_message=user_message,
        )

    def _build_candidate_actions(
        self,
        *,
        intent: IntentName,
        extracted_entities: dict[str, Any],
        session_state: WorkspaceSessionState,
    ) -> list[AgentAction]:
        """Generate a small set of operator-facing next actions for the current turn."""

        if intent == "greeting":
            return [
                AgentAction(
                    label="查询订单轨迹",
                    description="直接查询指定订单的运输状态和时间线。",
                    mode="input_required",
                    tool="resolve_waybill_number",
                    prompt="查询订单 #12345 的运输状态",
                ),
                AgentAction(
                    label="试算美国报价",
                    description="输入重量和件数后执行报价工具。",
                    mode="input_required",
                    tool="search_price",
                    prompt="先查一下美国报价 3kg 1件",
                ),
                AgentAction(
                    label="创建货运单",
                    description="进入建单工作流并收集必要字段。",
                    mode="input_required",
                    tool="create_order",
                    prompt="创建从深圳到洛杉矶的新货运单",
                ),
            ]

        if intent == "track_shipment":
            return [
                AgentAction(
                    label="解析单号",
                    description="先把客户参考号、系统单号或运单号归一化。",
                    mode="auto",
                    tool="resolve_waybill_number",
                    payload={"reference_number": extracted_entities.get("reference_number")},
                ),
                AgentAction(
                    label="抓取轨迹",
                    description="调用轨迹工具拉取最新运输节点。",
                    mode="auto",
                    tool="track_order",
                    payload={"reference_number": extracted_entities.get("reference_number")},
                ),
                AgentAction(
                    label="浏览最近订单",
                    description="如果单号不确定，可以先查看最近订单列表。",
                    mode="navigation",
                    tool="list_orders",
                    prompt="查询订单",
                ),
            ]

        if intent == "quote_shipment" or (intent == "provide_missing" and session_state.quote_draft):
            return [
                AgentAction(
                    label="补齐报价字段",
                    description="继续补重量、件数或目的国，直到满足报价条件。",
                    mode="input_required",
                    tool="search_price",
                ),
                AgentAction(
                    label="浏览支持渠道",
                    description="查看当前模拟环境下可用的物流渠道。",
                    mode="auto",
                    tool="list_channels",
                    prompt="查看渠道列表",
                ),
                AgentAction(
                    label="浏览支持目的地",
                    description="查看支持报价的国家或地区目录。",
                    mode="auto",
                    tool="list_destinations",
                    prompt="查看支持目的地",
                ),
            ]

        if intent == "create_shipment" or (intent == "provide_missing" and session_state.shipment_draft):
            return [
                AgentAction(
                    label="补齐建单字段",
                    description="继续补渠道、参考号、重量和收件信息。",
                    mode="input_required",
                    tool="create_order",
                ),
                AgentAction(
                    label="浏览渠道信息",
                    description="先看渠道目录，再决定使用哪个渠道建单。",
                    mode="auto",
                    tool="list_channels",
                    prompt="查看渠道列表",
                ),
                AgentAction(
                    label="创建预报单",
                    description="信息齐全后可以切换到预报单模式。",
                    mode="confirm_required",
                    tool="create_forecast_order",
                ),
            ]

        if intent == "order_lookup":
            return [
                AgentAction(
                    label="浏览最近订单",
                    description="查看最近生成的订单摘要和编号。",
                    mode="auto",
                    tool="list_orders",
                    prompt="查询订单",
                ),
                AgentAction(
                    label="继续查轨迹",
                    description="从最近订单中复制单号后继续追踪。",
                    mode="input_required",
                    tool="track_order",
                    prompt="查询订单 #12345 的运输状态",
                ),
            ]

        if intent == "confirm_action":
            return [
                AgentAction(
                    label="确认提交",
                    description="确认后会正式调用模拟建单工具。",
                    mode="confirm_required",
                    tool="create_order",
                    prompt="确认",
                ),
                AgentAction(
                    label="取消本次建单",
                    description="放弃当前草稿并清空待确认状态。",
                    mode="confirm_required",
                    prompt="取消",
                ),
            ]

        return [
            AgentAction(
                label="查运输状态",
                description="输入一个订单编号，查询轨迹和签收状态。",
                mode="input_required",
                tool="track_order",
                prompt="查询订单 #12345 的运输状态",
            ),
            AgentAction(
                label="查报价",
                description="输入国家、重量和件数，返回渠道试算结果。",
                mode="input_required",
                tool="search_price",
                prompt="先查一下美国报价 3kg 1件",
            ),
            AgentAction(
                label="创建货运单",
                description="开始收集建单字段并进入确认流。",
                mode="input_required",
                tool="create_order",
                prompt="创建从深圳到洛杉矶的新货运单",
            ),
        ]

    def _hydrate_city_defaults(self, extracted: dict[str, Any]) -> None:
        origin_city = extracted.get("origin_city")
        destination_city = extracted.get("destination_city")
        if origin_city:
            origin_defaults = CITY_DIRECTORY.get(origin_city.lower()) or CITY_DIRECTORY.get(origin_city)
            if origin_defaults:
                extracted.setdefault("origin_countrycode", origin_defaults["countrycode"])
        if destination_city:
            destination_defaults = CITY_DIRECTORY.get(destination_city.lower()) or CITY_DIRECTORY.get(destination_city)
            if destination_defaults:
                extracted.setdefault("countrycode", destination_defaults["countrycode"])
                extracted.setdefault("destination_countrycode", destination_defaults["countrycode"])
                extracted.setdefault("consigneecity", destination_city)
                extracted.setdefault("consigneeprovince", destination_defaults["province"])
                extracted.setdefault("consigneezipcode", destination_defaults["zipcode"])
