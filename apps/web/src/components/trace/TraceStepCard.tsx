import { Card, Tag } from 'tdesign-react';
import type { TraceStep } from '../../types/contracts';
import { formatTraceKind, formatTraceStatus, getTraceStatusTheme } from '../../utils/display';

interface TraceStepCardProps {
  step: TraceStep;
  emphasized?: boolean;
  index: number;
}

function summarizeStep(step: TraceStep) {
  if (step.kind === 'validation' && step.status === 'warning') {
    const missingSlots = Array.isArray(step.data?.missing_slots)
      ? step.data?.missing_slots.filter((item): item is string => typeof item === 'string')
      : [];
    const firstSlot = missingSlots[0];

    return {
      title: '需要补充少量信息',
      summary: firstSlot
        ? `当前还不能直接执行，我会一步一步带你补齐。先补 ${firstSlot} 就可以继续。`
        : '当前还不能直接执行，我会一步一步带你补齐，不需要一次性全部填写。',
    };
  }

  return {
    title: step.title,
    summary: step.summary,
  };
}

export function TraceStepCard({ step, emphasized, index }: TraceStepCardProps) {
  const copy = summarizeStep(step);

  return (
    <Card className={`trace-step-card${emphasized ? ' is-emphasized' : ''}`}>
        <div className="trace-step-card__header">
          <div className="trace-step-card__title">
            <span className="trace-step-card__index">{`0${index}`.slice(-2)}</span>
            <div>
              <span className="trace-step-card__kind">{formatTraceKind(step.kind)}</span>
              <strong>{copy.title}</strong>
            </div>
          </div>
          <Tag theme={getTraceStatusTheme(step.status)} variant="light">
            {formatTraceStatus(step.status)}
          </Tag>
        </div>
      <p>{copy.summary}</p>
      <time>{new Date(step.timestamp).toLocaleString('zh-CN')}</time>
    </Card>
  );
}
