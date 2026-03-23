import type { ConversationRequest, ConversationResponse, SessionTraceResponse } from '../types/contracts';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  postChat(payload: ConversationRequest) {
    return requestJson<ConversationResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getSessionTrace(sessionId: string) {
    return requestJson<SessionTraceResponse>(`/api/sessions/${sessionId}/trace`, {
      method: 'GET',
    });
  },
};
