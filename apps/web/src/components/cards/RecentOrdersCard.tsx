import { Card, Tag } from 'tdesign-react';
import type { RecentOrderRow, StatsCardData } from '../../types/contracts';

interface RecentOrdersCardProps {
  title: string;
  data: StatsCardData;
}

function asRecentOrderRows(rows?: Array<Record<string, unknown>>): RecentOrderRow[] {
  return (rows ?? []) as RecentOrderRow[];
}

function formatCreatedAt(value?: string) {
  if (!value) {
    return '时间待补充';
  }

  return value;
}

function buildDestination(row: RecentOrderRow) {
  const city = row.consigneecity;
  const province = row.consigneeprovince;
  const country = row.countryname ?? row.countrycode;

  return [city, province, country].filter(Boolean).join(' / ') || '目的地待补充';
}

export function RecentOrdersCard({ title, data }: RecentOrdersCardProps) {
  const rows = asRecentOrderRows(data.rows);

  return (
    <Card className="result-card" title={title}>
      <div className="recent-orders-list">
        {rows.map((row, index) => {
          const identifiers = row.identifiers ?? {};
          const orderNumber = identifiers.systemnumber ?? identifiers.waybillnumber ?? identifiers.customernumber ?? `ORDER-${index + 1}`;

          return (
            <article key={orderNumber} className="recent-order-card">
              <div className="recent-order-card__header">
                <div>
                  <p className="recent-order-card__eyebrow">Order {`0${index + 1}`.slice(-2)}</p>
                  <h3>{identifiers.systemnumber ?? '系统单号待生成'}</h3>
                </div>
                <div className="recent-order-card__tags">
                  {row.statusname ? (
                    <Tag theme="primary" variant="light">
                      {row.statusname}
                    </Tag>
                  ) : null}
                  {row.channelname ? <Tag variant="light">{row.channelname}</Tag> : null}
                </div>
              </div>

              <div className="recent-order-card__hero">
                <div className="recent-order-card__metric">
                  <span>运单号</span>
                  <strong>{identifiers.waybillnumber ?? '待生成'}</strong>
                </div>
                <div className="recent-order-card__metric">
                  <span>客户参考号</span>
                  <strong>{identifiers.customernumber ?? '未填写'}</strong>
                </div>
                <div className="recent-order-card__metric">
                  <span>目的地</span>
                  <strong>{buildDestination(row)}</strong>
                </div>
              </div>

              <div className="recent-order-card__grid">
                <div className="recent-order-card__item">
                  <span>收件人</span>
                  <strong>{row.consigneename ?? '待补充'}</strong>
                </div>
                <div className="recent-order-card__item">
                  <span>件数 / 重量</span>
                  <strong>{`${row.number ?? '--'} 件 / ${row.forecastweight ?? '--'} kg`}</strong>
                </div>
                <div className="recent-order-card__item">
                  <span>创建时间</span>
                  <strong>{formatCreatedAt(row.created_at)}</strong>
                </div>
                <div className="recent-order-card__item">
                  <span>跟踪号</span>
                  <strong>{identifiers.tracknumber ?? '暂无'}</strong>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </Card>
  );
}
