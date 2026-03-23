import { Button, Card, Tag } from 'tdesign-react';
import type { ConfirmationCardData, PendingAction } from '../../types/contracts';

interface ConfirmationCardProps {
  title: string;
  data: ConfirmationCardData;
  pendingAction?: PendingAction | null;
  loading?: boolean;
  sticky?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export function ConfirmationCard({
  title,
  data,
  pendingAction,
  loading,
  sticky,
  onConfirm,
  onCancel,
}: ConfirmationCardProps) {
  const entries = Object.entries(data.draft ?? {});

  return (
    <Card className={`result-card${sticky ? ' sticky-card' : ''}`} title={title}>
      <div className="result-card__header">
        <Tag theme="warning" variant="light">
          待确认
        </Tag>
        {pendingAction?.action_id ? <Tag variant="light">{pendingAction.action_id.slice(0, 8)}</Tag> : null}
      </div>

      <p className="confirmation-summary">{data.summary ?? pendingAction?.summary ?? '等待确认后继续建单。'}</p>

      <div className="confirmation-draft">
        {entries.map(([key, value]) => (
          <div key={key} className="confirmation-draft__item">
            <span>{key}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>

      {onConfirm && onCancel ? (
        <div className="confirmation-actions">
          <Button theme="primary" loading={loading} onClick={onConfirm}>
            确认
          </Button>
          <Button variant="outline" onClick={onCancel}>
            取消
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
