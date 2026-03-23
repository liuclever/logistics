import type { SessionSnapshot } from '../types/contracts';

const STORAGE_KEY = 'adk-logistics-recent-sessions';

export function loadRecentSessions(): SessionSnapshot[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw) as SessionSnapshot[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveRecentSessions(sessions: SessionSnapshot[]) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, 8)));
}

export function upsertRecentSession(
  current: SessionSnapshot[],
  snapshot: SessionSnapshot,
): SessionSnapshot[] {
  const filtered = current.filter((item) => item.sessionId !== snapshot.sessionId);
  const next = [snapshot, ...filtered].sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt));
  return next.slice(0, 8);
}
