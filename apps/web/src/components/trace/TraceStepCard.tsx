import { Card, Tag } from 'tdesign-react';
import type { TraceStep } from '../../types/contracts';

const statusThemeMap = {
  completed: 'success',
  running: 'primary',
  warning: 'warning',
  failed: 'danger',
} as const;

interface TraceStepCardProps {
  step: TraceStep;
  emphasized?: boolean;
}

export function TraceStepCard({ step, emphasized }: TraceStepCardProps) {
  return (
    <Card className={`trace-step-card${emphasized ? ' is-emphasized' : ''}`}>
      <div className="trace-step-card__header">
        <div>
          <span className="trace-step-card__kind">{step.kind}</span>
          <strong>{step.title}</strong>
        </div>
        <Tag theme={statusThemeMap[step.status]} variant="light">
          {step.status}
        </Tag>
      </div>
      <p>{step.summary}</p>
      <time>{new Date(step.timestamp).toLocaleString('zh-CN')}</time>
    </Card>
  );
}
