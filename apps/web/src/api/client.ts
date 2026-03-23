import type { ConversationRequest, ConversationResponse, SessionTraceResponse } from '../types/contracts';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new Error('后端服务不可达，请确认 8011 端口的 agent-server 已启动。');
  }

  if (!response.ok) {
    const text = await response.text();
    if (response.status === 404) {
      throw new Error('接口地址不存在。开发环境请确认前端代理已生效，后端运行在 127.0.0.1:8011。');
    }

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
