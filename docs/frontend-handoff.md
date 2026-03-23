# Frontend Handoff: ADK Logistics Agent Workbench

## 1. Project Positioning
- This is **not** a generic chat page.
- This is a **logistics AI workbench** with three visible layers:
  - conversation
  - execution trace
  - business result cards
- The backend is an **offline deterministic Google ADK agent server**.
- Frontend must behave like an enterprise operations console, not a consumer app.

## 2. Hard UI Rules
- Use **React + TypeScript**.
- Use **TDesign React** as the primary component library.
- Use **TDesign Icons** only.
- Style direction:
  - professional
  - calm
  - light business blue
  - clean white/blue-gray surfaces
- Allowed:
  - subtle frosted side panels
  - soft borders
  - low-contrast shadows
- Forbidden:
  - flashy gradients
  - glassmorphism over the whole page
  - emoji
  - neon effects
  - overly playful illustrations
- Tone:
  - business first
  - slightly lively only in welcome or empty states
  - never childish

## 3. Page Layout
- Build a single-page workbench with 3 columns.

### Left Column
- Width: fixed desktop sidebar
- Content:
  - app logo / title
  - current session list
  - quick prompts
  - lightweight KPI cards
- Suggested quick prompts:
  - `查询订单 #12345 的运输状态`
  - `创建从深圳到洛杉矶的新货运单`
  - `先查一下美国报价`

### Center Column
- Main chat workspace
- Contains:
  - top toolbar
  - message list
  - result cards rendered inline after assistant replies
  - input box
  - send button
- Input interaction:
  - submit on button click
  - support `Enter` submit and `Shift+Enter` newline

### Right Column
- Execution and observability panel
- Contains:
  - trace step timeline
  - current intent / workflow
  - pending action status
  - raw structured summary blocks if useful

## 4. Required Components
- `WorkbenchShell`
- `SidebarSessions`
- `QuickPromptList`
- `ChatThread`
- `MessageBubble`
- `Composer`
- `TraceTimeline`
- `TraceStepCard`
- `ShipmentSummaryCard`
- `TrackTimelineCard`
- `PriceTableCard`
- `ConfirmationCard`
- `StatsCard`

## 5. Backend API Contracts

### POST `/api/chat`
Request:
```json
{
  "sessionId": "optional-string",
  "message": "创建从深圳到洛杉矶的新货运单",
  "mode": "offline-demo"
}
```

Response:
```json
{
  "sessionId": "uuid",
  "reply": "assistant text",
  "traceSteps": [],
  "cards": [],
  "pendingAction": null,
  "sessionState": {}
}
```

### GET `/api/sessions/{sessionId}/trace`
Response:
```json
{
  "sessionId": "uuid",
  "traceSteps": [],
  "sessionState": {}
}
```

## 6. Frontend Data Shapes

### `traceSteps[]`
Each item contains:
- `step_id`
- `title`
- `status`
  - `completed`
  - `running`
  - `warning`
  - `failed`
- `summary`
- `kind`
  - `decision`
  - `tool`
  - `validation`
  - `summary`
- `timestamp`
- `data`

### `cards[]`
Each card contains:
- `id`
- `kind`
  - `track_timeline`
  - `shipment_summary`
  - `price_table`
  - `confirmation`
  - `error`
  - `stats`
- `title`
- `data`

### `pendingAction`
When present:
- show sticky confirmation UI
- current backend flow only uses:
  - `kind = confirm_create_order`

## 7. Required UI Behaviours

### Chat Flow
- Keep full thread in local state.
- Every assistant response should render:
  - one text bubble
  - zero or more cards
- Persist `sessionId` after first successful request.

### Trace Flow
- Replace right panel trace with latest `traceSteps`.
- Highlight step status with TDesign status color tokens.
- Most recent step should be visually strongest.

### Confirmation Flow
- If `pendingAction` exists:
  - show a dedicated confirmation card
  - expose two buttons:
    - confirm
    - cancel
- Confirm button sends message: `确认`
- Cancel button sends message: `取消`
- Do not invent separate backend endpoints for confirmation.

### Inline Result Rendering
- `shipment_summary`:
  - show system number
  - waybill number
  - customer reference
  - remote flag
- `track_timeline`:
  - vertical event timeline
  - newest event first
- `price_table`:
  - table with channel, aging, total cost, currency, note
- `error`:
  - red toned but still professional
- `stats`:
  - small dashboard cards or compact table

## 8. Charts
- Use professional charts only.
- Suggested charts in left or right panel:
  - tracking queries count
  - quote queries count
  - successful orders
  - failed orders
- Recommended chart types:
  - compact bar chart
  - donut / ring chart
- Keep charts secondary to the chat workflow.

## 9. Visual Tokens
- Suggested direction:
  - page background: very light blue-gray
  - sidebar background: semi-opaque cool white
  - main content: solid white
  - accent: restrained blue
  - warning: amber
  - danger: red
  - success: green
- Typography:
  - use TDesign defaults or a clean sans stack
  - no decorative fonts

## 10. Responsive Behaviour
- Desktop first.
- On narrow screens:
  - stack right trace panel below chat
  - collapse left sidebar to icons or drawer
- Minimum acceptable mobile behavior:
  - send message
  - view latest assistant reply
  - view latest confirmation card

## 11. Do Not Do
- Do not expose backend internal chain-of-thought.
- Do not fabricate fields not returned by backend.
- Do not add fake logistics maps or unrelated illustrations.
- Do not hardcode demo replies on the frontend.
- Do not create a second state machine that conflicts with backend session state.

## 12. State Management Guidance
- Keep frontend state simple.
- Recommended state:
  - `sessionId`
  - `messages`
  - `traceSteps`
  - `sessionState`
  - `loading`
  - `error`
- Recommended networking:
  - a typed API client layer
  - optional React Query for request state

## 13. Suggested File Structure
```text
src/
  api/
    client.ts
  components/
    workbench/
    chat/
    trace/
    cards/
  hooks/
    useChatSession.ts
  types/
    contracts.ts
  pages/
    WorkbenchPage.tsx
  App.tsx
  main.tsx
```

## 14. First Implementation Priority
1. Build typed API client.
2. Build page shell with 3-column layout.
3. Connect chat submit and session persistence.
4. Render assistant text and `cards`.
5. Render trace panel.
6. Render confirmation flow.
7. Add charts and polish.

## 15. Acceptance Standard
- A user can:
  - query `#12345`
  - see shipment results and trace
  - start a create-shipment flow
  - answer missing-slot prompts
  - confirm creation
  - see final shipment summary
- The page looks like an enterprise operations console.
- The UI never feels like a toy demo.
