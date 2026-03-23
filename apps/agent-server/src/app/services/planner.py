"""Deterministic planner used by the offline ADK logistics agent."""

from __future__ import annotations

import re
from typing import Any

from app.domain.models import AgentPlan, IntentName, QuoteDraft, ShipmentDraft, WorkspaceSessionState
from app.mock_gateway.catalog import CHANNELS, CITY_DIRECTORY


YES_WORDS = {"确认", "好的", "ok", "yes", "y", "确认下单", "提交"}
NO_WORDS = {"取消", "不用了", "no", "n", "拒绝", "先不创建"}


class DeterministicPlanner:
    """Rule-based planner that emulates enterprise workflow routing."""

    def plan(self, message: str, session_state: WorkspaceSessionState) -> AgentPlan:
        normalized = message.strip()
        lowered = normalized.lower()
        extracted = self.extract_entities(normalized)

        if session_state.pending_action:
            intent: IntentName = "confirm_action"
            return AgentPlan(
                intent=intent,
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.99,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        if session_state.shipment_draft and self._looks_like_slot_answer(lowered):
            return AgentPlan(
                intent="provide_missing",
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.93,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        if any(keyword in lowered for keyword in ["查价", "报价", "price", "quote"]):
            return AgentPlan(
                intent="quote_shipment",
                selected_workflow="QuoteWorkflow",
                confidence=0.95,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        if any(keyword in lowered for keyword in ["创建", "下单", "货运单", "发一票", "建单"]):
            return AgentPlan(
                intent="create_shipment",
                selected_workflow="CreateShipmentWorkflow",
                confidence=0.97,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        if any(keyword in lowered for keyword in ["运输状态", "轨迹", "track", "物流状态", "查询订单"]):
            return AgentPlan(
                intent="track_shipment",
                selected_workflow="ReferenceResolutionWorkflow",
                confidence=0.95,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        if any(keyword in lowered for keyword in ["订单列表", "订单查询", "分页查询", "最近订单"]):
            return AgentPlan(
                intent="order_lookup",
                selected_workflow="OrderLookupWorkflow",
                confidence=0.88,
                extracted_entities=extracted,
                missing_slots=[],
                user_message=normalized,
            )

        return AgentPlan(
            intent="unknown",
            selected_workflow="UnknownWorkflow",
            confidence=0.4,
            extracted_entities=extracted,
            missing_slots=[],
            user_message=normalized,
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
        return any(
            token in lowered
            for token in ["渠道", "参考号", "收件人", "地址", "kg", "公斤", "件", "从", "到"]
        )

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

