import { Card } from 'tdesign-react';
import type { PendingAction, ResponseCard } from '../../types/contracts';
import { ConfirmationCard } from './ConfirmationCard';
import { PriceTableCard } from './PriceTableCard';
import { ShipmentSummaryCard } from './ShipmentSummaryCard';
import { TrackTimelineCard } from './TrackTimelineCard';

interface CardRendererProps {
  card: ResponseCard;
  pendingAction?: PendingAction | null;
  loading?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export function CardRenderer({ card, pendingAction, loading, onConfirm, onCancel }: CardRendererProps) {
  switch (card.kind) {
    case 'shipment_summary':
      return <ShipmentSummaryCard title={card.title} data={card.data} />;
    case 'track_timeline':
      return <TrackTimelineCard title={card.title} data={card.data} />;
    case 'price_table':
      return <PriceTableCard title={card.title} data={card.data} />;
    case 'confirmation':
      return (
        <ConfirmationCard
          title={card.title}
          data={card.data}
          pendingAction={pendingAction}
          loading={loading}
          onConfirm={onConfirm}
          onCancel={onCancel}
        />
      );
    case 'error':
      return (
        <Card className="result-card result-card--error" title={card.title}>
          <p>{card.data.message ?? '请求处理失败。'}</p>
        </Card>
      );
    case 'stats':
      return (
        <Card className="result-card" title={card.title}>
          <div className="stats-table">
            {(card.data.rows ?? []).map((row, index) => (
              <div key={`stats-row-${index}`} className="stats-table__row">
                {Object.entries(row).map(([key, value]) => (
                  <div key={key}>
                    <span>{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </Card>
      );
    default:
      return null;
  }
}
