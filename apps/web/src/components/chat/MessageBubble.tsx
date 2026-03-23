import type { ChatMessage } from '../../types/contracts';

function formatTime(value: string) {
  try {
    return new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <article className={`message-bubble ${message.role === 'user' ? 'is-user' : 'is-assistant'}`}>
      <div className="message-bubble__meta">
        <span>{message.role === 'user' ? '你' : '物流助手'}</span>
        <time>{formatTime(message.createdAt)}</time>
      </div>
      <div className="message-bubble__body">{message.text}</div>
    </article>
  );
}
