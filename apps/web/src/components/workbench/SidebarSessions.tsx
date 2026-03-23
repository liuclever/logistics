import { Button, Card, Tag } from 'tdesign-react';
import type { SessionSnapshot } from '../../types/contracts';

interface SidebarSessionsProps {
  sessions: SessionSnapshot[];
  activeSessionId?: string;
  onSelect: (session: SessionSnapshot) => void;
  onNewSession: () => void;
}

function formatTime(value: string) {
  try {
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function SidebarSessions({ sessions, activeSessionId, onSelect, onNewSession }: SidebarSessionsProps) {
  return (
    <Card className="panel-card" title="当前会话">
      <div className="session-actions">
        <Button theme="primary" block onClick={onNewSession}>
          新建工作台会话
        </Button>
      </div>

      <div className="session-list">
        {sessions.length === 0 ? (
          <div className="empty-inline">
            <p>当前浏览器还没有会话记录。</p>
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.sessionId === activeSessionId;
            return (
              <button
                key={session.sessionId}
                type="button"
                className={`session-item${isActive ? ' is-active' : ''}`}
                onClick={() => onSelect(session)}
              >
                <div className="session-item__top">
                  <strong>{session.title}</strong>
                  {isActive ? (
                    <Tag size="small" theme="primary" variant="light">
                      当前
                    </Tag>
                  ) : null}
                </div>
                <p>{session.sessionId}</p>
                <span>{formatTime(session.updatedAt)}</span>
              </button>
            );
          })
        )}
      </div>
    </Card>
  );
}
