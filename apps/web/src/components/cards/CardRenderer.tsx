import { Card } from 'tdesign-react';
import type { PendingAction, ResponseCard } from '../../types/contracts';
import { ActionListCard } from './ActionListCard';
import { ConfirmationCard } from './ConfirmationCard';
import { PriceTableCard } from './PriceTableCard';
import { RecentOrdersCard } from './RecentOrdersCard';
import { ShipmentSummaryCard } from './ShipmentSummaryCard';
import { TrackTimelineCard } from './TrackTimelineCard';

interface CardRendererProps {
  card: ResponseCard;
  pendingAction?: PendingAction | null;
  loading?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
  onSelectAction?: (prompt: string) => void;
}

export function CardRenderer({ card, pendingAction, loading, onConfirm, onCancel, onSelectAction }: CardRendererProps) {
  switch (card.kind) {
    case 'shipment_summary':
      return <ShipmentSummaryCard title={card.title} data={card.data} />;
    case 'track_timeline':
      if (!card.data.trackItems?.length) {
        return null;
      }
      return <TrackTimelineCard title={card.title} data={card.data} />;
    case 'price_table':
      if (!card.data.rows?.length) {
        return null;
      }
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
    case 'action_list':
      if (!card.data.actions?.length) {
        return null;
      }
      return <ActionListCard title={card.title} data={card.data} onSelectAction={onSelectAction} />;
    case 'error':
      return (
        <Card className="result-card result-card--error" title={card.title}>
          <p>{card.data.message ?? '请求处理失败。'}</p>
        </Card>
      );
    case 'stats':
      if (!card.data.rows?.length) {
        return null;
      }
      return <RecentOrdersCard title={card.title} data={card.data} />;
    default:
      return null;
  }
}
