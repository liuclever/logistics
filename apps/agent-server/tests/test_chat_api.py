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
    assert payload["traceSteps"][0]["status"] in {"completed", "running", "warning", "failed"}
    assert payload["traceSteps"][0]["kind"] in {"decision", "tool", "validation", "summary"}


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


def test_quote_workflow_continues_after_slot_answer() -> None:
    """A quote follow-up like `3kg` should continue the quote workflow instead of falling back."""

    client = TestClient(create_app())
    first = client.post(
        "/api/chat",
        json={"message": "先查一下美国报价", "mode": "offline-demo"},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert "重量" in first_payload["reply"]

    second = client.post(
        "/api/chat",
        json={"sessionId": first_payload["sessionId"], "message": "3kg", "mode": "offline-demo"},
    )
    assert second.status_code == 200
    second_payload = second.json()
    assert "件数" in second_payload["reply"]
    assert second_payload["sessionState"]["quote_draft"]["weight"] == 3.0
    assert any(card["kind"] == "action_list" for card in second_payload["cards"])


def test_greeting_returns_operator_style_welcome() -> None:
    """A plain greeting should not fall into the clumsy unknown-intent fallback copy."""

    client = TestClient(create_app())
    response = client.post(
        "/api/chat",
        json={"message": "你好", "mode": "offline-demo"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "我目前支持三类高价值动作" not in payload["reply"]
    assert "你好，我可以直接帮你处理物流工作" in payload["reply"]
    assert any(card["kind"] == "action_list" for card in payload["cards"])


def test_explicit_order_query_overrides_stale_quote_draft() -> None:
    """An explicit order-query message should not be hijacked by an unfinished quote draft."""

    client = TestClient(create_app())
    first = client.post(
        "/api/chat",
        json={"message": "先查一下美国报价", "mode": "offline-demo"},
    )
    assert first.status_code == 200
    session_id = first.json()["sessionId"]

    second = client.post(
        "/api/chat",
        json={"sessionId": session_id, "message": "查询订单3kg", "mode": "offline-demo"},
    )
    assert second.status_code == 200
    second_payload = second.json()
    assert "最近订单" in second_payload["cards"][0]["title"]
    assert second_payload["sessionState"]["quote_draft"] is None


def test_quote_workflow_accepts_numeric_piece_answer() -> None:
    """A numeric-only follow-up should be accepted as the quote piece count."""

    client = TestClient(create_app())
    first = client.post(
        "/api/chat",
        json={"message": "先查一下美国报价", "mode": "offline-demo"},
    )
    session_id = first.json()["sessionId"]

    second = client.post(
        "/api/chat",
        json={"sessionId": session_id, "message": "3kg", "mode": "offline-demo"},
    )
    assert second.status_code == 200
    assert "件数" in second.json()["reply"]

    third = client.post(
        "/api/chat",
        json={"sessionId": session_id, "message": "55", "mode": "offline-demo"},
    )
    assert third.status_code == 200
    third_payload = third.json()
    assert any(card["kind"] == "price_table" for card in third_payload["cards"])


def test_quote_card_contains_frontend_friendly_price_fields() -> None:
    """Quote card rows should expose normalized cost and currency fields for the web table."""

    client = TestClient(create_app())
    response = client.post(
        "/api/chat",
        json={"message": "先查一下美国报价 3kg 1件", "mode": "offline-demo"},
    )
    assert response.status_code == 200
    payload = response.json()
    price_card = next(card for card in payload["cards"] if card["kind"] == "price_table")
    first_row = price_card["data"]["rows"][0]
    assert first_row["total_cost"] == 113.0
    assert first_row["currency"] == "CNY"


def test_unknown_intent_returns_candidate_actions() -> None:
    """The fallback branch should still return an action list instead of a dead-end message."""

    client = TestClient(create_app())
    response = client.post(
        "/api/chat",
        json={"message": "帮我搞一下那个东西", "mode": "offline-demo"},
    )
    assert response.status_code == 200
    payload = response.json()
    action_card = next(card for card in payload["cards"] if card["kind"] == "action_list")
    assert len(action_card["data"]["actions"]) >= 2
    assert action_card["data"]["actions"][0]["tool"] in {"track_order", "search_price", "create_order"}
    assert len(action_card["data"]["thinkingFlow"]) >= 1
