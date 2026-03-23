"""Wrap mock logistics capabilities as ADK-compatible function tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google.adk.tools import FunctionTool

from app.domain.models import ToolResult
from app.mock_gateway.catalog import MockLogisticsGateway


@dataclass
class LogisticsToolRegistry:
    """Expose deterministic logistics functions and their ADK tool wrappers."""

    gateway: MockLogisticsGateway
    tools: list[FunctionTool] = field(init=False)

    def __post_init__(self) -> None:
        # Keep the public tool surface aligned with the task scope.
        self.tools = [
            FunctionTool(self.track_order),
            FunctionTool(self.create_order),
            FunctionTool(self.create_forecast_order),
            FunctionTool(self.search_price),
            FunctionTool(self.list_orders),
            FunctionTool(self.resolve_waybill_number),
            FunctionTool(self.list_channels),
            FunctionTool(self.list_destinations),
            FunctionTool(self.list_product_types),
            FunctionTool(self.list_currencies),
        ]

    def track_order(self, search_number: str) -> dict[str, Any]:
        return self.gateway.track_order(search_number).model_dump(mode="json")

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.gateway.create_order(payload, forecast=False).model_dump(mode="json")

    def create_forecast_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.gateway.create_order(payload, forecast=True).model_dump(mode="json")

    def search_price(
        self,
        destination_countrycode: str,
        destination_city: str | None,
        weight: float,
        piece: int,
        channelid: str | None = None,
    ) -> dict[str, Any]:
        return self.gateway.search_price(
            destination_countrycode=destination_countrycode,
            destination_city=destination_city,
            weight=weight,
            piece=piece,
            channelid=channelid,
        ).model_dump(mode="json")

    def list_orders(self) -> dict[str, Any]:
        return self.gateway.list_orders().model_dump(mode="json")

    def resolve_waybill_number(self, search_number: str) -> dict[str, Any]:
        return self.gateway.resolve_waybill_number(search_number).model_dump(mode="json")

    def list_channels(self) -> dict[str, Any]:
        return self.gateway.list_channels().model_dump(mode="json")

    def list_destinations(self) -> dict[str, Any]:
        return self.gateway.list_destinations().model_dump(mode="json")

    def list_product_types(self) -> dict[str, Any]:
        return self.gateway.list_product_types().model_dump(mode="json")

    def list_currencies(self) -> dict[str, Any]:
        return self.gateway.list_currencies().model_dump(mode="json")

    @staticmethod
    def unwrap(result: dict[str, Any]) -> ToolResult[Any]:
        """Recover a typed result object after a tool call."""

        return ToolResult[Any].model_validate(result)

