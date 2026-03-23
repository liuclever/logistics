"""Core domain and API models for the logistics agent workbench."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, Literal, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field


IntentName = Literal[
    "greeting",
    "track_shipment",
    "create_shipment",
    "quote_shipment",
    "order_lookup",
    "confirm_action",
    "provide_missing",
    "unknown",
]

WorkflowName = Literal[
    "TrackShipmentWorkflow",
    "CreateShipmentWorkflow",
    "QuoteWorkflow",
    "OrderLookupWorkflow",
    "ReferenceResolutionWorkflow",
    "UnknownWorkflow",
]

CardKind = Literal[
    "track_timeline",
    "shipment_summary",
    "price_table",
    "confirmation",
    "action_list",
    "error",
    "stats",
]

TraceStatus = Literal["completed", "running", "warning", "failed"]
TraceKind = Literal["decision", "tool", "validation", "summary"]
PendingActionKind = Literal["confirm_create_order"]
ActionMode = Literal["auto", "input_required", "confirm_required", "navigation"]


class TrackEvent(BaseModel):
    """Represents a single logistics tracking event."""

    trackdate: str
    trackdate_utc8: str
    location: str
    info: str
    responsecode: str


class OrderIdentifier(BaseModel):
    """Stores the three identifier types used by the logistics API."""

    customernumber: str
    systemnumber: str
    waybillnumber: str
    tracknumber: str | None = None
    shortnumber: str | None = None


class OrderSummary(BaseModel):
    """Normalized order shape shared by multiple workflows."""

    identifiers: OrderIdentifier
    status: str
    statusname: str
    channelid: str
    channelname: str
    countrycode: str
    countryname: str
    consigneename: str
    consigneecity: str
    consigneezipcode: str
    consigneeprovince: str
    consigneeaddress1: str
    forecastweight: float
    number: int
    is_remote: bool = False
    created_at: str
    items: list[dict[str, Any]] = Field(default_factory=list)
    track_items: list[TrackEvent] = Field(default_factory=list)


class ShipmentDraft(BaseModel):
    """Conversation-safe shipment draft used for slot filling."""

    customernumber1: str | None = None
    channelid: str | None = None
    number: int | None = None
    forecastweight: float | None = None
    countrycode: str | None = None
    consigneename: str | None = None
    consigneeaddress1: str | None = None
    consigneecity: str | None = None
    consigneezipcode: str | None = None
    consigneeprovince: str | None = None
    origin_city: str | None = None
    origin_countrycode: str | None = "CN"
    goodstypecode: str = "WPX"
    isbattery: int = 0
    ismagnet: int = 0
    isliquid: int = 0
    ispowder: int = 0
    isinsurance: int = 0
    mode: Literal["draft", "forecast"] = "draft"
    note: str | None = None
    producttypepkid: str | None = "1"
    source_message: str | None = None


class QuoteDraft(BaseModel):
    """Conversation-safe quote request used for slot filling."""

    destination_countrycode: str | None = None
    destination_city: str | None = None
    weight: float | None = None
    piece: int | None = None
    goodstype: str = "WPX"
    producttypepkid: str = "1"
    channelid: str | None = None


class PendingAction(BaseModel):
    """Represents a user confirmation step."""

    kind: PendingActionKind
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)


class TraceStep(BaseModel):
    """Represents one visible step in the agent execution timeline."""

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    status: TraceStatus
    summary: str
    kind: TraceKind
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: dict[str, Any] | None = None


class ResponseCard(BaseModel):
    """Frontend-ready response card."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: CardKind
    title: str
    data: dict[str, Any]


class AgentAction(BaseModel):
    """A concrete next action that the workbench can show to the operator."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    description: str
    mode: ActionMode
    tool: str | None = None
    prompt: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ThinkingStep(BaseModel):
    """Productized reasoning step exposed to the UI instead of raw chain-of-thought."""

    step_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    title: str
    content: str


class AgentPlan(BaseModel):
    """Planner output used by the deterministic orchestration layer."""

    intent: IntentName
    selected_workflow: WorkflowName
    confidence: float
    extracted_entities: dict[str, Any] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    candidate_actions: list[AgentAction] = Field(default_factory=list)
    user_message: str


class WorkspaceStats(BaseModel):
    """Simple counters shown on the workbench dashboard."""

    total_messages: int = 0
    successful_orders: int = 0
    failed_orders: int = 0
    tracking_queries: int = 0
    quote_queries: int = 0


class WorkspaceSessionState(BaseModel):
    """Long-lived session state persisted in the ADK session store."""

    shipment_draft: ShipmentDraft | None = None
    quote_draft: QuoteDraft | None = None
    pending_action: PendingAction | None = None
    last_plan: AgentPlan | None = None
    last_trace: list[TraceStep] = Field(default_factory=list)
    last_cards: list[ResponseCard] = Field(default_factory=list)
    stats: WorkspaceStats = Field(default_factory=WorkspaceStats)


class ConversationRequest(BaseModel):
    """Request contract for the chat API."""

    sessionId: str | None = None
    message: str
    mode: Literal["offline-demo"] = "offline-demo"


class ConversationResponse(BaseModel):
    """Response contract for the chat API."""

    sessionId: str
    reply: str
    traceSteps: list[TraceStep]
    cards: list[ResponseCard]
    pendingAction: PendingAction | None = None
    sessionState: WorkspaceSessionState


class SessionTraceResponse(BaseModel):
    """Read-only trace endpoint response."""

    sessionId: str
    traceSteps: list[TraceStep]
    sessionState: WorkspaceSessionState


TData = TypeVar("TData")


class ToolResult(BaseModel, Generic[TData]):
    """Standardized result wrapper used by every internal tool."""

    success: bool
    code: int
    msg: str
    data: TData | None = None
