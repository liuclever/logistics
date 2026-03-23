import { Card } from 'tdesign-react';
import type { ChatMessage, PendingAction } from '../../types/contracts';
import { CardRenderer } from '../cards/CardRenderer';
import { MessageBubble } from './MessageBubble';

interface ChatThreadProps {
  messages: ChatMessage[];
  pendingAction?: PendingAction | null;
  loading?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
  suggestions?: string[];
  onSelectSuggestion?: (value: string) => void;
  onSelectAction?: (value: string) => void;
}

export function ChatThread({
  messages,
  pendingAction,
  loading,
  onConfirm,
  onCancel,
  suggestions = [],
  onSelectSuggestion,
  onSelectAction,
}: ChatThreadProps) {
  if (messages.length === 0) {
    return (
      <Card className="chat-welcome">
        <div className="welcome-block">
          <h2>有什么我能帮你的吗？</h2>
          {suggestions.length ? (
            <div className="welcome-actions">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  className="welcome-action"
                  onClick={() => onSelectSuggestion?.(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </Card>
    );
  }

  return (
    <div className="chat-thread">
      {messages.map((message) => (
        <section key={message.id} className="thread-item">
          <MessageBubble message={message} />
          {message.role === 'assistant' && message.cards?.length ? (
            <div className="inline-cards">
              {message.cards.map((card) => (
                <CardRenderer
                  key={card.id}
                  card={card}
                  pendingAction={pendingAction}
                  loading={loading}
                  onConfirm={onConfirm}
                  onCancel={onCancel}
                  onSelectAction={onSelectAction}
                />
              ))}
            </div>
          ) : null}
        </section>
      ))}
    </div>
  );
}
