import { Card, Tag } from 'tdesign-react';
import type { TrackTimelineCardData } from '../../types/contracts';

interface TrackTimelineCardProps {
  title: string;
  data: TrackTimelineCardData;
}

export function TrackTimelineCard({ title, data }: TrackTimelineCardProps) {
  const events = [...(data.trackItems ?? [])];

  return (
    <Card className="result-card" title={title}>
      <div className="result-card__header">
        {data.searchNumber ? <Tag variant="light">{data.searchNumber}</Tag> : null}
        {data.status ? (
          <Tag theme="primary" variant="light">
            {data.status}
          </Tag>
        ) : null}
      </div>

      <div className="timeline-list">
        {events.length === 0 ? (
          <div className="empty-inline">
            <p>暂无轨迹节点。</p>
          </div>
        ) : (
          events.map((event, index) => (
            <div key={`${event.trackdate_utc8 ?? event.trackdate ?? 'event'}-${index}`} className="timeline-item">
              <div className="timeline-item__line" />
              <div className="timeline-item__content">
                <strong>{event.location ?? '未知节点'}</strong>
                <span>{event.trackdate_utc8 ?? event.trackdate ?? '--'}</span>
                <p>{event.info ?? '暂无说明'}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
