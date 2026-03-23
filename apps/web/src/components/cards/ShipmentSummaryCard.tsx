import { Card, Tag } from 'tdesign-react';
import type { ShipmentSummaryCardData } from '../../types/contracts';

interface ShipmentSummaryCardProps {
  title: string;
  data: ShipmentSummaryCardData;
}

export function ShipmentSummaryCard({ title, data }: ShipmentSummaryCardProps) {
  const pairs = [
    { label: '系统单号', value: data.systemnumber },
    { label: '运单号', value: data.waybillnumber },
    { label: '客户参考号', value: data.customernumber ?? data.customernumber1 },
    { label: '跟踪号', value: data.tracknumber },
  ].filter((item) => item.value);

  return (
    <Card className="result-card" title={title}>
      <div className="result-card__header">
        {data.status ? (
          <Tag theme="primary" variant="light">
            {data.status}
          </Tag>
        ) : null}
        {typeof data.is_remote === 'boolean' ? (
          <Tag theme={data.is_remote ? 'warning' : 'success'} variant="light">
            {data.is_remote ? '偏远地区' : '非偏远'}
          </Tag>
        ) : null}
      </div>
      <div className="summary-grid">
        {pairs.map((item) => (
          <div key={item.label} className="summary-grid__item">
            <span>{item.label}</span>
            <strong>{String(item.value)}</strong>
          </div>
        ))}
      </div>
    </Card>
  );
}
