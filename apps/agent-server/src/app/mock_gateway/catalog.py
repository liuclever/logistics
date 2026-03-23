"""Static mock data and API-like behaviours based on the logistics document."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.models import OrderIdentifier, OrderSummary, ToolResult, TrackEvent


CHANNELS: list[dict[str, Any]] = [
    {
        "channelid": "HK_TNT",
        "channeltype": "专线",
        "channelname": "香港TNT",
        "channelnamecn": "香港TNT",
        "channelnameen": "Hong Kong TNT",
    },
    {
        "channelid": "US_FAST",
        "channeltype": "快递",
        "channelname": "美国快线",
        "channelnamecn": "美国快线",
        "channelnameen": "US Express Line",
    },
    {
        "channelid": "CN_EMS",
        "channeltype": "快递",
        "channelname": "中国邮政",
        "channelnamecn": "中国邮政",
        "channelnameen": "China Post",
    },
]

DESTINATIONS: list[dict[str, str]] = [
    {"code": "US", "name": "United States", "desttype": "country"},
    {"code": "CN", "name": "China", "desttype": "country"},
    {"code": "GB", "name": "United Kingdom", "desttype": "country"},
]

PRODUCT_TYPES: list[dict[str, str]] = [
    {"pkid": "1", "name": "普货"},
    {"pkid": "6", "name": "电子配件"},
]

CURRENCIES: list[dict[str, str]] = [
    {"code": "USD", "name": "美元"},
    {"code": "CNY", "name": "人民币"},
]

CITY_DIRECTORY: dict[str, dict[str, str]] = {
    "深圳": {"countrycode": "CN", "province": "Guangdong", "zipcode": "518000"},
    "深圳市": {"countrycode": "CN", "province": "Guangdong", "zipcode": "518000"},
    "洛杉矶": {"countrycode": "US", "province": "CA", "zipcode": "90001"},
    "los angeles": {"countrycode": "US", "province": "CA", "zipcode": "90001"},
    "l.a.": {"countrycode": "US", "province": "CA", "zipcode": "90001"},
    "london": {"countrycode": "GB", "province": "London", "zipcode": "EC1A 1AA"},
}


def _build_seed_orders() -> dict[str, OrderSummary]:
    """Builds a predictable in-memory order store."""

    signed_tracks = [
        TrackEvent(
            trackdate="2026-03-20 11:30:00",
            trackdate_utc8="2026-03-20 19:30:00",
            location="OXNARD, CA, US",
            info="已签收",
            responsecode="OT001",
        ),
        TrackEvent(
            trackdate="2026-03-19 04:10:00",
            trackdate_utc8="2026-03-19 12:10:00",
            location="Ontario, CA, US",
            info="离开分拣中心",
            responsecode="OT001",
        ),
    ]
    draft_tracks = [
        TrackEvent(
            trackdate="2026-03-22 08:15:00",
            trackdate_utc8="2026-03-22 16:15:00",
            location="Shenzhen, CN",
            info="信息已录入，等待揽收",
            responsecode="OT000",
        )
    ]
    return {
        "12345": OrderSummary(
            identifiers=OrderIdentifier(
                customernumber="12345",
                systemnumber="SYS202603230001",
                waybillnumber="WB202603230001",
                tracknumber="1Z76V3R40448621361",
                shortnumber="230001",
            ),
            status="Sign",
            statusname="已签收",
            channelid="HK_TNT",
            channelname="香港TNT",
            countrycode="US",
            countryname="United States",
            consigneename="Alice Johnson",
            consigneecity="Los Angeles",
            consigneezipcode="90001",
            consigneeprovince="CA",
            consigneeaddress1="123 Main Street",
            forecastweight=2.4,
            number=1,
            is_remote=False,
            created_at="2026-03-18 09:00:00",
            items=[{"enname": "Phone Case", "quantity": 12, "price": 4.5}],
            track_items=signed_tracks,
        ),
        "DRAFT-001": OrderSummary(
            identifiers=OrderIdentifier(
                customernumber="DRAFT-001",
                systemnumber="SYS202603220101",
                waybillnumber="WB202603220101",
                tracknumber="1ZTEST0000001",
                shortnumber="220101",
            ),
            status="Draft",
            statusname="草稿",
            channelid="US_FAST",
            channelname="美国快线",
            countrycode="US",
            countryname="United States",
            consigneename="Demo Consignee",
            consigneecity="Los Angeles",
            consigneezipcode="90001",
            consigneeprovince="CA",
            consigneeaddress1="500 Demo Avenue",
            forecastweight=1.2,
            number=1,
            is_remote=False,
            created_at="2026-03-22 08:10:00",
            items=[],
            track_items=draft_tracks,
        ),
    }


class MockLogisticsGateway:
    """Simulates the external logistics APIs using deterministic in-memory data."""

    def __init__(self) -> None:
        self._orders = _build_seed_orders()
        self._order_counter = 8000

    def list_channels(self) -> ToolResult[list[dict[str, Any]]]:
        return ToolResult(success=True, code=0, msg="调用成功", data=deepcopy(CHANNELS))

    def list_destinations(self) -> ToolResult[list[dict[str, Any]]]:
        return ToolResult(success=True, code=0, msg="调用成功", data=deepcopy(DESTINATIONS))

    def list_product_types(self) -> ToolResult[list[dict[str, Any]]]:
        return ToolResult(success=True, code=0, msg="调用成功", data=deepcopy(PRODUCT_TYPES))

    def list_currencies(self) -> ToolResult[list[dict[str, Any]]]:
        return ToolResult(success=True, code=0, msg="调用成功", data=deepcopy(CURRENCIES))

    def list_orders(self) -> ToolResult[list[dict[str, Any]]]:
        data = [order.model_dump(mode="json") for order in self._orders.values()]
        return ToolResult(success=True, code=0, msg="调用成功", data=data)

    def resolve_waybill_number(self, search_number: str) -> ToolResult[dict[str, Any]]:
        order = self._find_order(search_number)
        if not order:
            return ToolResult(success=False, code=-1, msg="单号系统中不存在", data=None)
        return ToolResult(
            success=True,
            code=0,
            msg="获取单号成功",
            data=order.identifiers.model_dump(mode="json"),
        )

    def track_order(self, search_number: str) -> ToolResult[list[dict[str, Any]]]:
        order = self._find_order(search_number)
        if not order:
            return ToolResult(success=False, code=-1, msg="未找到对应运单", data=None)
        data = [
            {
                "searchNumber": search_number,
                "systemnumber": order.identifiers.systemnumber,
                "waybillnumber": order.identifiers.waybillnumber,
                "tracknumber": order.identifiers.tracknumber,
                "countrycode": order.countrycode,
                "orderstatus": order.status,
                "orderstatusName": order.statusname,
                "trackItems": [item.model_dump(mode="json") for item in order.track_items],
            }
        ]
        return ToolResult(success=True, code=0, msg="success", data=data)

    def search_price(
        self,
        *,
        destination_countrycode: str,
        destination_city: str | None,
        weight: float,
        piece: int,
        channelid: str | None = None,
    ) -> ToolResult[list[dict[str, Any]]]:
        if destination_countrycode not in {item["code"] for item in DESTINATIONS}:
            return ToolResult(success=False, code=422, msg="目的地暂不支持报价", data=None)
        if weight <= 0 or piece <= 0:
            return ToolResult(success=False, code=422, msg="重量和件数必须大于 0", data=None)

        base_quotes = [
            {
                "channelid": "HK_TNT",
                "channelname": "香港TNT",
                "aging": "5-7 working days",
                "totalCost": round(weight * 35 + piece * 8, 2),
                "totalCostCcy": "CNY",
                "note": "适合普货和稳定签收场景",
            },
            {
                "channelid": "US_FAST",
                "channelname": "美国快线",
                "aging": "4-6 working days",
                "totalCost": round(weight * 42 + piece * 6, 2),
                "totalCostCcy": "CNY",
                "note": "时效更快，适合高时效订单",
            },
        ]
        filtered = [quote for quote in base_quotes if not channelid or quote["channelid"] == channelid]
        if not filtered:
            return ToolResult(success=False, code=404, msg="指定渠道不支持当前报价请求", data=None)
        return ToolResult(success=True, code=0, msg="调用成功", data=filtered)

    def create_order(self, payload: dict[str, Any], *, forecast: bool = False) -> ToolResult[list[dict[str, Any]]]:
        customer_ref = payload["customernumber1"]
        existing = self._orders.get(customer_ref)
        if forecast and existing:
            return ToolResult(success=False, code=-1, msg="客户参考号已存在，不允许重复创建预报单", data=None)
        if existing and not forecast and existing.status == "Draft":
            updated = existing.model_copy(
                update={
                    "forecastweight": float(payload["forecastweight"]),
                    "number": int(payload["number"]),
                    "consigneename": payload["consigneename"],
                    "consigneeaddress1": payload["consigneeaddress1"],
                }
            )
            self._orders[customer_ref] = updated
            return ToolResult(
                success=True,
                code=0,
                msg="调用成功",
                data=[self._build_create_order_row(updated, "草稿单已更新")],
            )

        self._order_counter += 1
        system_number = f"SYS202603{self._order_counter:06d}"
        waybill_number = f"WB202603{self._order_counter:06d}"
        now = datetime.now(UTC)
        status = "Forecast" if forecast else "Draft"
        status_name = "预报" if forecast else "草稿"
        order = OrderSummary(
            identifiers=OrderIdentifier(
                customernumber=customer_ref,
                systemnumber=system_number,
                waybillnumber=waybill_number,
                tracknumber=f"1ZMOCK{self._order_counter:010d}",
                shortnumber=str(self._order_counter),
            ),
            status=status,
            statusname=status_name,
            channelid=payload["channelid"],
            channelname=self._channel_name(payload["channelid"]),
            countrycode=payload["countrycode"],
            countryname=self._country_name(payload["countrycode"]),
            consigneename=payload["consigneename"],
            consigneecity=payload["consigneecity"],
            consigneezipcode=payload["consigneezipcode"],
            consigneeprovince=payload["consigneeprovince"],
            consigneeaddress1=payload["consigneeaddress1"],
            forecastweight=float(payload["forecastweight"]),
            number=int(payload["number"]),
            is_remote=payload["consigneezipcode"].startswith("9"),
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            items=[],
            track_items=[
                TrackEvent(
                    trackdate=now.strftime("%Y-%m-%d %H:%M:%S"),
                    trackdate_utc8=(now + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
                    location=f"{payload['origin_city']}, CN",
                    info="订单已创建，等待系统揽收",
                    responsecode="OT100",
                )
            ],
        )
        self._orders[customer_ref] = order
        return ToolResult(
            success=True,
            code=0,
            msg="调用成功",
            data=[self._build_create_order_row(order, "下单成功")],
        )

    def _find_order(self, search_number: str) -> OrderSummary | None:
        normalized = search_number.replace("#", "").strip()
        if normalized in self._orders:
            return self._orders[normalized]
        for order in self._orders.values():
            identifiers = order.identifiers
            if normalized in {
                identifiers.customernumber,
                identifiers.systemnumber,
                identifiers.waybillnumber,
                identifiers.tracknumber,
            }:
                return order
        return None

    def _channel_name(self, channelid: str) -> str:
        for channel in CHANNELS:
            if channel["channelid"] == channelid:
                return str(channel["channelname"])
        return channelid

    def _country_name(self, code: str) -> str:
        for destination in DESTINATIONS:
            if destination["code"] == code:
                return str(destination["name"])
        return code

    def _build_create_order_row(self, order: OrderSummary, message: str) -> dict[str, Any]:
        return {
            "code": 0,
            "msg": message,
            "customernumber": order.identifiers.customernumber,
            "systemnumber": order.identifiers.systemnumber,
            "waybillnumber": order.identifiers.waybillnumber,
            "shortnumber": order.identifiers.shortnumber,
            "isRemote": order.is_remote,
            "childs": [],
        }
