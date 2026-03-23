import { Card } from 'tdesign-react';

interface StatsCardProps {
  stats: {
    totalMessages: number;
    trackingQueries: number;
    quoteQueries: number;
    successfulOrders: number;
    failedOrders: number;
  };
}

const statItems = [
  { key: 'trackingQueries', label: '轨迹查询' },
  { key: 'quoteQueries', label: '报价查询' },
  { key: 'successfulOrders', label: '成功建单' },
  { key: 'failedOrders', label: '失败建单' },
] as const;

export function StatsCard({ stats }: StatsCardProps) {
  return (
    <Card className="panel-card" title="工作台指标">
      <div className="stats-grid">
        <div className="stats-highlight">
          <span>累计消息</span>
          <strong>{stats.totalMessages}</strong>
        </div>
        {statItems.map((item) => (
          <div key={item.key} className="stats-mini">
            <span>{item.label}</span>
            <strong>{stats[item.key]}</strong>
          </div>
        ))}
      </div>
    </Card>
  );
}
