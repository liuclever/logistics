export type TraceStatus = 'completed' | 'running' | 'warning' | 'failed';
export type TraceKind = 'decision' | 'tool' | 'validation' | 'summary';
export type PendingActionKind = 'confirm_create_order';
export type ResponseCardKind =
  | 'track_timeline'
  | 'shipment_summary'
  | 'price_table'
  | 'confirmation'
  | 'error'
  | 'stats';

export interface TraceStep {
  step_id: string;
  title: string;
  status: TraceStatus;
  summary: string;
  kind: TraceKind;
  timestamp: string;
  data?: Record<string, unknown> | null;
}

export interface PendingAction {
  kind: PendingActionKind;
  action_id: string;
  summary: string;
  payload: Record<string, unknown>;
}

export interface WorkspaceStats {
  total_messages?: number;
  successful_orders?: number;
  failed_orders?: number;
  tracking_queries?: number;
  quote_queries?: number;
}

export interface SessionPlan {
  intent?: string;
  selected_workflow?: string;
  confidence?: number;
  extracted_entities?: Record<string, unknown>;
  missing_slots?: string[];
  user_message?: string;
}

export interface WorkspaceSessionState {
  shipment_draft?: Record<string, unknown> | null;
  quote_draft?: Record<string, unknown> | null;
  pending_action?: PendingAction | null;
  last_plan?: SessionPlan | null;
  last_trace?: TraceStep[];
  last_cards?: ResponseCard[];
  stats?: WorkspaceStats;
}

export interface ShipmentSummaryCardData {
  systemnumber?: string;
  waybillnumber?: string;
  tracknumber?: string;
  customernumber?: string;
  customernumber1?: string;
  countrycode?: string;
  status?: string;
  is_remote?: boolean;
  [key: string]: unknown;
}

export interface TrackTimelineEvent {
  trackdate?: string;
  trackdate_utc8?: string;
  location?: string;
  info?: string;
  responsecode?: string;
}

export interface TrackTimelineCardData {
  searchNumber?: string;
  status?: string;
  trackItems?: TrackTimelineEvent[];
}

export interface PriceTableRow {
  channel?: string;
  channelname?: string;
  aging?: string;
  total_cost?: number | string;
  totalcost?: number | string;
  currency?: string;
  note?: string;
  [key: string]: unknown;
}

export interface PriceTableCardData {
  rows: PriceTableRow[];
}

export interface ConfirmationCardData {
  summary?: string;
  draft?: Record<string, unknown>;
  actionId?: string;
}

export interface ErrorCardData {
  message?: string;
  searchNumber?: string;
  [key: string]: unknown;
}

export interface StatsCardData {
  rows?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export type ResponseCard =
  | {
      id: string;
      kind: 'shipment_summary';
      title: string;
      data: ShipmentSummaryCardData;
    }
  | {
      id: string;
      kind: 'track_timeline';
      title: string;
      data: TrackTimelineCardData;
    }
  | {
      id: string;
      kind: 'price_table';
      title: string;
      data: PriceTableCardData;
    }
  | {
      id: string;
      kind: 'confirmation';
      title: string;
      data: ConfirmationCardData;
    }
  | {
      id: string;
      kind: 'error';
      title: string;
      data: ErrorCardData;
    }
  | {
      id: string;
      kind: 'stats';
      title: string;
      data: StatsCardData;
    };

export interface ConversationRequest {
  sessionId?: string;
  message: string;
  mode: 'offline-demo';
}

export interface ConversationResponse {
  sessionId: string;
  reply: string;
  traceSteps: TraceStep[];
  cards: ResponseCard[];
  pendingAction: PendingAction | null;
  sessionState: WorkspaceSessionState;
}

export interface SessionTraceResponse {
  sessionId: string;
  traceSteps: TraceStep[];
  sessionState: WorkspaceSessionState;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  cards?: ResponseCard[];
  createdAt: string;
}

export interface SessionSnapshot {
  sessionId: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
  traceSteps: TraceStep[];
  sessionState: WorkspaceSessionState | null;
  pendingAction: PendingAction | null;
}
