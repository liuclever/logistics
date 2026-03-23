import { Card } from 'tdesign-react';
import type { PriceTableCardData } from '../../types/contracts';

interface PriceTableCardProps {
  title: string;
  data: PriceTableCardData;
}

function normalizeCost(row: PriceTableCardData['rows'][number]) {
  return row.total_cost ?? row.totalcost ?? '--';
}

export function PriceTableCard({ title, data }: PriceTableCardProps) {
  return (
    <Card className="result-card" title={title}>
      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>渠道</th>
              <th>时效</th>
              <th>总成本</th>
              <th>币种</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            {(data.rows ?? []).map((row, index) => (
              <tr key={`${row.channel ?? row.channelname ?? 'row'}-${index}`}>
                <td>{String(row.channelname ?? row.channel ?? '--')}</td>
                <td>{String(row.aging ?? '--')}</td>
                <td>{String(normalizeCost(row))}</td>
                <td>{String(row.currency ?? '--')}</td>
                <td>{String(row.note ?? '--')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
