"""API-level tests for the offline ADK logistics backend."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_track_order_happy_path() -> None:
    """The seeded order should resolve and render tracking data."""

    client = TestClient(create_app())
    response = client.post(
        "/api/chat",
        json={"message": "查询订单 #12345 的运输状态", "mode": "offline-demo"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "已签收" in payload["reply"]
    assert any(card["kind"] == "track_timeline" for card in payload["cards"])
    assert any(step["title"] == "调用 track_order" for step in payload["traceSteps"])


def test_create_order_requires_slots_then_confirmation() -> None:
    """The create workflow should collect slots, request confirmation, and create the order."""

    client = TestClient(create_app())
    first = client.post(
        "/api/chat",
        json={"message": "创建从深圳到洛杉矶的新货运单", "mode": "offline-demo"},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert "渠道" in first_payload["reply"]

    second = client.post(
        "/api/chat",
        json={
            "sessionId": first_payload["sessionId"],
            "message": "渠道用香港TNT 参考号 SZ-LA-1001 1件 2kg 收件人 Alice 地址 123 Main Street",
            "mode": "offline-demo",
        },
    )
    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["pendingAction"] is not None
    assert any(card["kind"] == "confirmation" for card in second_payload["cards"])

    third = client.post(
        "/api/chat",
        json={"sessionId": first_payload["sessionId"], "message": "确认", "mode": "offline-demo"},
    )
    assert third.status_code == 200
    third_payload = third.json()
    assert "模拟建单已经完成" in third_payload["reply"]
    assert any(card["kind"] == "shipment_summary" for card in third_payload["cards"])


def test_trace_endpoint_returns_latest_session_trace() -> None:
    """The trace endpoint should reflect the last executed workflow."""

    client = TestClient(create_app())
    chat = client.post(
        "/api/chat",
        json={"message": "先查一下美国报价 2kg 1件", "mode": "offline-demo"},
    )
    assert chat.status_code == 200
    session_id = chat.json()["sessionId"]

    trace = client.get(f"/api/sessions/{session_id}/trace")
    assert trace.status_code == 200
    trace_payload = trace.json()
    assert trace_payload["sessionId"] == session_id
    assert len(trace_payload["traceSteps"]) >= 1
