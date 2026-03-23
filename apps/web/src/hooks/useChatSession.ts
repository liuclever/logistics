import { useCallback, useMemo, useState } from 'react';
import { apiClient } from '../api/client';
import type {
  ChatMessage,
  PendingAction,
  SessionSnapshot,
  TraceStep,
  WorkspaceSessionState,
} from '../types/contracts';
import { loadRecentSessions, saveRecentSessions, upsertRecentSession } from '../utils/storage';

function createMessage(role: ChatMessage['role'], text: string, cards?: ChatMessage['cards']): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    text,
    cards,
    createdAt: new Date().toISOString(),
  };
}

function deriveTitle(messages: ChatMessage[], sessionId: string) {
  const firstUserMessage = messages.find((item) => item.role === 'user')?.text.trim();
  if (!firstUserMessage) {
    return `会话 ${sessionId.slice(0, 8)}`;
  }

  return firstUserMessage.slice(0, 24);
}

function persistSnapshot(
  existing: SessionSnapshot[],
  sessionId: string,
  messages: ChatMessage[],
  traceSteps: TraceStep[],
  sessionState: WorkspaceSessionState | null,
  pendingAction: PendingAction | null,
) {
  const snapshot: SessionSnapshot = {
    sessionId,
    title: deriveTitle(messages, sessionId),
    updatedAt: new Date().toISOString(),
    messages,
    traceSteps,
    sessionState,
    pendingAction,
  };

  const next = upsertRecentSession(existing, snapshot);
  saveRecentSessions(next);
  return next;
}

export function useChatSession() {
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([]);
  const [sessionState, setSessionState] = useState<WorkspaceSessionState | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentSessions, setRecentSessions] = useState<SessionSnapshot[]>(() => loadRecentSessions());

  const stats = useMemo(
    () => ({
      totalMessages: messages.length,
      trackingQueries: sessionState?.stats?.tracking_queries ?? 0,
      quoteQueries: sessionState?.stats?.quote_queries ?? 0,
      successfulOrders: sessionState?.stats?.successful_orders ?? 0,
      failedOrders: sessionState?.stats?.failed_orders ?? 0,
    }),
    [messages.length, sessionState],
  );

  const startNewSession = useCallback(() => {
    setSessionId(undefined);
    setMessages([]);
    setTraceSteps([]);
    setSessionState(null);
    setPendingAction(null);
    setError(null);
    setLoading(false);
  }, []);

  const submitMessage = useCallback(
    async (rawMessage: string) => {
      const message = rawMessage.trim();
      if (!message || loading) {
        return;
      }

      const nextUserMessage = createMessage('user', message);
      const nextThread = [...messages, nextUserMessage];

      setMessages(nextThread);
      setError(null);
      setLoading(true);

      try {
        const response = await apiClient.postChat({
          sessionId,
          message,
          mode: 'offline-demo',
        });

        const assistantMessage = createMessage('assistant', response.reply, response.cards);
        const resolvedMessages = [...nextThread, assistantMessage];
        const resolvedPendingAction = response.pendingAction ?? response.sessionState.pending_action ?? null;

        setSessionId(response.sessionId);
        setMessages(resolvedMessages);
        setTraceSteps(response.traceSteps);
        setSessionState(response.sessionState);
        setPendingAction(resolvedPendingAction);
        setRecentSessions((current) =>
          persistSnapshot(
            current,
            response.sessionId,
            resolvedMessages,
            response.traceSteps,
            response.sessionState,
            resolvedPendingAction,
          ),
        );
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : '请求失败');
      } finally {
        setLoading(false);
      }
    },
    [loading, messages, sessionId],
  );

  const openSession = useCallback(async (snapshot: SessionSnapshot) => {
    setSessionId(snapshot.sessionId);
    setMessages(snapshot.messages);
    setTraceSteps(snapshot.traceSteps);
    setSessionState(snapshot.sessionState);
    setPendingAction(snapshot.pendingAction);
    setError(null);

    try {
      const latest = await apiClient.getSessionTrace(snapshot.sessionId);
      const latestPendingAction = latest.sessionState.pending_action ?? null;
      setTraceSteps(latest.traceSteps);
      setSessionState(latest.sessionState);
      setPendingAction(latestPendingAction);
      setRecentSessions((current) =>
        persistSnapshot(
          current,
          snapshot.sessionId,
          snapshot.messages,
          latest.traceSteps,
          latest.sessionState,
          latestPendingAction,
        ),
      );
    } catch {
      // Preserve cached session state when trace refresh is unavailable.
    }
  }, []);

  const confirmPendingAction = useCallback(async () => {
    if (!pendingAction) {
      return;
    }

    await submitMessage('确认');
  }, [pendingAction, submitMessage]);

  const cancelPendingAction = useCallback(async () => {
    if (!pendingAction) {
      return;
    }

    await submitMessage('取消');
  }, [pendingAction, submitMessage]);

  return {
    sessionId,
    messages,
    traceSteps,
    sessionState,
    pendingAction,
    loading,
    error,
    recentSessions,
    stats,
    submitMessage,
    startNewSession,
    openSession,
    confirmPendingAction,
    cancelPendingAction,
  };
}
