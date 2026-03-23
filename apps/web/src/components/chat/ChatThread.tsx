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
}

export function ChatThread({ messages, pendingAction, loading, onConfirm, onCancel }: ChatThreadProps) {
  if (messages.length === 0) {
    return (
      <Card className="chat-welcome">
        <div className="welcome-block">
          <p className="eyebrow">Logistics Operations Console</p>
          <h2>不是聊天玩具，而是业务工作台。</h2>
          <p>
            你可以直接查询订单、发起建单、追踪轨迹和进入确认流。右侧会同步显示执行轨迹与当前工作流状态。
          </p>
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
                />
              ))}
            </div>
          ) : null}
        </section>
      ))}
    </div>
  );
}
